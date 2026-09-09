# Написание плагинов

Плагины общаются с ядром через REST запросы. Используйте `PluginSDK` из папки `sdk/`.

```python
from plugin_sdk import sdk
plugin = sdk("my_plugin")
# plugin.port, plugin.core_url
```
