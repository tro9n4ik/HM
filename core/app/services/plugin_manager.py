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
            # Zip-Slip protection
            for member in zip_ref.infolist():
                # zip_ref.extract safely normalizes paths in modern python, but
                # verifying the absolute path doesn't escape plugin_path is safer
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError(f"Zip-slip attempt detected: {member.filename}")

                # Check resolved path
                extracted_path = (plugin_path / member.filename).resolve()
                if not str(extracted_path).startswith(str(plugin_path.resolve())):
                    raise ValueError(f"Zip-slip attempt detected: {member.filename}")

                zip_ref.extract(member, plugin_path)

        # Inject SDK into the plugin root
        sdk_source = Path(__file__).parent.parent.parent.parent / "plugins" / "sdk" / "plugin_sdk.py"
        if sdk_source.exists():
            shutil.copy2(sdk_source, plugin_path / "plugin_sdk.py")

        return str(plugin_path)

    def setup_environment(self, plugin_path_str: str, pip_index_url: str = None) -> bool:
        import subprocess
        import sys

        plugin_path = Path(plugin_path_str).resolve()
        venv_path = plugin_path / "venv"

        try:
            # Create venv without --symlinks if needed, but standard is fine
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True)

            req_path = plugin_path / "requirements.txt"
            if req_path.exists():
                python_exe = venv_path / "bin" / "python"
                if os.name == "nt":
                    python_exe = venv_path / "Scripts" / "python.exe"

                cmd = [str(python_exe), "-m", "pip", "install", "-r", str(req_path)]
                if pip_index_url:
                    cmd.extend(["-i", pip_index_url])

                subprocess.run(cmd, check=True, capture_output=True)

            return True
        except subprocess.CalledProcessError as e:
            return False

    def _get_free_port(self, db, start=8100, end=8200) -> int:
        from app.models.plugin import Plugin
        used_ports = [p.port for p in db.query(Plugin).all() if p.port is not None]

        import socket
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', port)) == 0

        for port in range(start, end + 1):
            if port not in used_ports and not is_port_in_use(port):
                return port
        raise Exception("No free ports available in the configured range")

    def start_plugin(self, plugin, db) -> bool:
        import subprocess
        import os
        from app.models.system import SystemSetting, ActivityLog

        if plugin.port is None:
            port_range_setting = db.query(SystemSetting).filter_by(key="plugin_port_range").first()
            start, end = 8100, 8200
            if port_range_setting and port_range_setting.value:
                try:
                    start_str, end_str = port_range_setting.value.split("-")
                    start, end = int(start_str), int(end_str)
                except:
                    pass
            try:
                plugin.port = self._get_free_port(db, start, end)
                db.commit()
            except Exception as e:
                plugin.status = "failed"
                plugin.last_error = str(e)
                db.commit()
                return False

        plugin_path = Path(plugin.path).resolve()
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
            db.add(ActivityLog(source="plugin_manager", message=f"Started plugin: {plugin.name} (v{plugin.version})"))
            db.commit()
            return True
        except Exception as e:
            plugin.status = "failed"
            plugin.last_error = str(e)
            db.add(ActivityLog(source="plugin_manager", message=f"Failed to start plugin: {plugin.name}. Error: {e}"))
            db.commit()
            return False

    def stop_plugin(self, plugin, db):
        import psutil
        from app.models.system import ActivityLog

        proc = self.running_processes.get(plugin.id)
        if proc:
            try:
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            del self.running_processes[plugin.id]

        plugin.status = "stopped"
        db.add(ActivityLog(source="plugin_manager", message=f"Stopped plugin: {plugin.name} (v{plugin.version})"))
        db.commit()

    async def healthcheck_loop(self, db_maker):
        import asyncio
        import httpx
        from app.models.plugin import Plugin
        from starlette.concurrency import run_in_threadpool

        while True:
            try:
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
