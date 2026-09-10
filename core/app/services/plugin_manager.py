import os
import zipfile
import json
from pathlib import Path
from typing import Dict, Any

class PluginManager:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.plugins_dir = self.data_dir / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.running_processes = {}

    def unpack_plugin(self, zip_path: str, plugin_name: str) -> str:
        plugin_path = self.plugins_dir / plugin_name

        import shutil
        if plugin_path.exists():
            shutil.rmtree(plugin_path)

        plugin_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(plugin_path)

        return str(plugin_path)

    def setup_environment(self, plugin_path_str: str, pip_index_url: str = None) -> bool:
        import subprocess
        import sys

        plugin_path = Path(plugin_path_str)
        venv_path = plugin_path / "venv"

        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True)

            req_path = plugin_path / "requirements.txt"
            if req_path.exists():
                pip_exe = venv_path / "bin" / "pip"
                if os.name == "nt":
                    pip_exe = venv_path / "Scripts" / "pip.exe"

                cmd = [str(pip_exe), "install", "-r", str(req_path)]
                if pip_index_url:
                    cmd.extend(["-i", pip_index_url])

                subprocess.run(cmd, check=True, capture_output=True)

            return True
        except subprocess.CalledProcessError as e:
            return False

    def _get_free_port(self, db, start=8100, end=8200) -> int:
        from app.models.plugin import Plugin
        used_ports = [p.port for p in db.query(Plugin).all() if p.port is not None]
        for port in range(start, end + 1):
            if port not in used_ports:
                return port
        raise Exception("No free ports available in the configured range")

    def start_plugin(self, plugin, db) -> bool:
        import subprocess
        import os
        from app.models.system import SystemSetting

        if plugin.port is None:
            port_range_setting = db.query(SystemSetting).filter_by(key="plugin_port_range").first()
            start, end = 8100, 8200
            if port_range_setting and port_range_setting.value:
                try:
                    start_str, end_str = port_range_setting.value.split("-")
                    start, end = int(start_str), int(end_str)
                except:
                    pass
            plugin.port = self._get_free_port(db, start, end)
            db.commit()

        plugin_path = Path(plugin.path)
        venv_path = plugin_path / "venv"
        python_exe = venv_path / "bin" / "python"
        if os.name == "nt":
            python_exe = venv_path / "Scripts" / "python.exe"

        main_py = plugin_path / "main.py"

        env = os.environ.copy()
        env.pop("SECRET_KEY", None)
        env.pop("DATABASE_URL", None)
        env["PLUGIN_PORT"] = str(plugin.port)
        env["PLUGIN_ID"] = plugin.id
        env["CORE_INTERNAL_URL"] = os.environ.get("CORE_INTERNAL_URL", "http://127.0.0.1:8142")

        log_file_path = plugin_path / "plugin.log"

        try:
            with open(log_file_path, "a") as log_file:
                proc = subprocess.Popen(
                    [str(python_exe), str(main_py)],
                    env=env,
                    cwd=str(plugin_path),
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
            self.running_processes[plugin.id] = proc

            plugin.status = "starting"
            db.commit()
            return True
        except Exception as e:
            plugin.status = "failed"
            plugin.last_error = str(e)
            db.commit()
            return False

    def stop_plugin(self, plugin, db):
        proc = self.running_processes.get(plugin.id)
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except:
                proc.kill()
            del self.running_processes[plugin.id]

        plugin.status = "stopped"
        db.commit()

    async def healthcheck_loop(self, db_maker):
        import asyncio
        import httpx
        from app.models.plugin import Plugin
        from starlette.concurrency import run_in_threadpool

        while True:
            try:
                # Run DB fetch in a separate thread so it doesn't block the async loop
                def get_plugins():
                    db = db_maker()
                    try:
                        return db.query(Plugin).filter(Plugin.status.in_(["starting", "running", "degraded"])).all()
                    finally:
                        db.close()

                plugins = await run_in_threadpool(get_plugins)

                async with httpx.AsyncClient(timeout=3.0) as client:
                    for plugin in plugins:
                        if not plugin.port:
                            continue

                        proc = self.running_processes.get(plugin.id)
                        if proc and proc.poll() is not None:
                            def update_failed(pid, retcode):
                                db = db_maker()
                                p = db.query(Plugin).filter(Plugin.id == pid).first()
                                if p:
                                    p.status = "failed"
                                    p.last_error = f"Process exited with code {retcode}"
                                    db.commit()
                                db.close()

                            await run_in_threadpool(update_failed, plugin.id, proc.returncode)
                            del self.running_processes[plugin.id]
                            continue

                        try:
                            resp = await client.get(f"http://127.0.0.1:{plugin.port}/health")
                            if resp.status_code == 200:
                                if plugin.status != "running":
                                    def update_running(pid):
                                        db = db_maker()
                                        p = db.query(Plugin).filter(Plugin.id == pid).first()
                                        if p:
                                            p.status = "running"
                                            p.last_error = None
                                            db.commit()
                                        db.close()
                                    await run_in_threadpool(update_running, plugin.id)
                            else:
                                if plugin.status != "degraded":
                                    def update_degraded(pid, status_code):
                                        db = db_maker()
                                        p = db.query(Plugin).filter(Plugin.id == pid).first()
                                        if p:
                                            p.status = "degraded"
                                            p.last_error = f"Healthcheck failed with {status_code}"
                                            db.commit()
                                        db.close()
                                    await run_in_threadpool(update_degraded, plugin.id, resp.status_code)
                        except Exception as e:
                            if plugin.status == "running":
                                def update_degraded_err(pid, err_msg):
                                    db = db_maker()
                                    p = db.query(Plugin).filter(Plugin.id == pid).first()
                                    if p:
                                        p.status = "degraded"
                                        p.last_error = err_msg
                                        db.commit()
                                    db.close()
                                await run_in_threadpool(update_degraded_err, plugin.id, str(e))

            except Exception as e:
                print(f"Healthcheck loop error: {e}")

            await asyncio.sleep(10)

    def get_plugin_logs(self, plugin, lines=100) -> str:
        plugin_path = Path(plugin.path)
        log_file_path = plugin_path / "plugin.log"
        if not log_file_path.exists():
            return ""

        try:
            import os
            with open(log_file_path, "rb") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                block_size = 4096
                blocks = []
                lines_found = 0
                pos = file_size
                while pos > 0 and lines_found <= lines:
                    read_size = min(block_size, pos)
                    pos -= read_size
                    f.seek(pos)
                    block = f.read(read_size)
                    lines_found += block.count(b'\n')
                    blocks.append(block)

                blocks.reverse()
                data = b"".join(blocks)
                last_lines = data.decode('utf-8', errors='replace').splitlines()[-lines:]
                res = "\n".join(last_lines)
                if data.endswith(b"\n") and last_lines:
                    res += "\n"
                return res
        except Exception as e:
            return f"Error reading logs: {e}"

plugin_manager = PluginManager(os.getenv("DATA_DIR", "./dev_data"))
