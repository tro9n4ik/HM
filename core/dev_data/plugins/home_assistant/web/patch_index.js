const fs = require('fs');

let html = fs.readFileSync('plugins/home_assistant/web/index.html', 'utf8');

const groupSection = `
        <!-- Groups Tab -->
        <div id="content-groups" class="space-y-6">
            <!-- Group Management Block -->
            <div class="card p-6 shadow-sm mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-gray-800">Мои группы Telegram</h2>
                    <button onclick="openGroupModal()" class="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">Создать группу</button>
                </div>

                <div class="mb-4 flex items-center gap-2">
                    <input type="checkbox" id="only_custom_groups" class="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50" onchange="toggleOnlyCustomGroups(this.checked)">
                    <label for="only_custom_groups" class="text-sm text-gray-700">Показывать в Telegram только мои группы (скрыть авто-группы)</label>
                </div>

                <div id="custom-groups-list" class="space-y-3">
                    <!-- Groups injected here -->
                </div>
            </div>

            <!-- Modal for Group Editing -->
            <div id="group-modal" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-6 border w-full max-w-2xl shadow-lg rounded-lg bg-white">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-bold text-gray-900" id="group-modal-title">Создать группу</h3>
                        <button onclick="closeGroupModal()" class="text-gray-400 hover:text-gray-600">&times;</button>
                    </div>

                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-1">Название группы</label>
                        <input type="text" id="group-name-input" class="w-full rounded border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50" placeholder="Например: Свет в гостиной">
                        <input type="hidden" id="group-original-name">
                    </div>

                    <div class="mb-4">
                        <input type="text" id="entity-search-input" onkeyup="filterEntities()" class="w-full rounded border-gray-300 shadow-sm text-sm" placeholder="Поиск устройств...">
                    </div>

                    <div class="h-64 overflow-y-auto border border-gray-200 rounded p-2 mb-4" id="entities-checkbox-list">
                        <!-- Checkboxes injected here -->
                    </div>

                    <div class="flex justify-end gap-3">
                        <button onclick="closeGroupModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200">Отмена</button>
                        <button onclick="saveGroup()" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Сохранить</button>
                    </div>
                </div>
            </div>

            <!-- Entities Block -->
            <div class="dark-mode p-6 rounded-lg">
                <div id="domains-container" class="space-y-8">
                    <!-- Dynamic content injected here -->
                </div>
            </div>
        </div>
`;

html = html.replace(/<div id="content-groups" class="dark-mode p-6 rounded-lg">[\s\S]*?<\/div>[\s]*<\/div>/, groupSection);

const jsAdditions = `
        const loadConfigForGroups = async () => {
            if (!state.plugin_id) return;
            try {
                const res = await fetch(\`/api/plugins/\${state.plugin_id}/config\`);
                state.config = await res.json();

                document.getElementById('only_custom_groups').checked = state.config.only_custom_groups === 'true' || state.config.only_custom_groups === true;
                renderCustomGroups();
            } catch (e) {
                console.error("Failed to load config for groups", e);
            }
        };

        const toggleOnlyCustomGroups = async (checked) => {
            try {
                const configData = { ...state.config, only_custom_groups: checked ? "true" : "false" };
                const res = await fetch(\`/api/plugins/\${state.plugin_id}/config\`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ config: configData })
                });
                if (res.ok) {
                    state.config.only_custom_groups = checked ? "true" : "false";
                }
            } catch (err) {
                console.error("Failed to save flag", err);
            }
        };

        const getParsedGroups = () => {
            if (!state.config || !state.config.tg_groups) return {};
            try {
                if (typeof state.config.tg_groups === 'string') {
                    return JSON.parse(state.config.tg_groups);
                }
                return state.config.tg_groups;
            } catch (e) {
                return {};
            }
        };

        const renderCustomGroups = () => {
            const container = document.getElementById('custom-groups-list');
            const groups = getParsedGroups();
            container.innerHTML = '';

            const groupNames = Object.keys(groups);
            if (groupNames.length === 0) {
                container.innerHTML = '<div class="text-sm text-gray-500 italic">Нет созданных групп</div>';
                return;
            }

            groupNames.forEach(name => {
                const count = groups[name].length;
                const div = document.createElement('div');
                div.className = 'flex justify-between items-center p-3 border border-gray-200 rounded hover:bg-gray-50 transition-colors bg-white';
                div.innerHTML = \`
                    <div>
                        <div class="font-medium text-gray-800">\${name}</div>
                        <div class="text-xs text-gray-500">Устройств: \${count}</div>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="editGroup('\${name}')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 border border-gray-300">Изменить</button>
                        <button onclick="deleteGroup('\${name}')" class="px-3 py-1 bg-red-50 text-red-600 rounded text-sm hover:bg-red-100 border border-red-200">Удалить</button>
                    </div>
                \`;
                container.appendChild(div);
            });
        };

        const renderEntitiesListForModal = (selectedEntities = []) => {
            const container = document.getElementById('entities-checkbox-list');
            container.innerHTML = '';

            if (!state.entities) return;

            state.entities.forEach(ent => {
                const name = ent.attributes.friendly_name || ent.entity_id;
                const isSelected = selectedEntities.includes(ent.entity_id);

                const label = document.createElement('label');
                label.className = 'entity-cb-item flex items-center gap-3 p-2 hover:bg-gray-50 border-b border-gray-100 cursor-pointer';
                label.innerHTML = \`
                    <input type="checkbox" class="rounded text-blue-600 entity-checkbox" value="\${ent.entity_id}" \${isSelected ? 'checked' : ''}>
                    <div>
                        <div class="text-sm font-medium text-gray-800">\${name}</div>
                        <div class="text-xs text-gray-500 font-mono entity-id-text">\${ent.entity_id}</div>
                    </div>
                \`;
                container.appendChild(label);
            });
        };

        const filterEntities = () => {
            const term = document.getElementById('entity-search-input').value.toLowerCase();
            const items = document.querySelectorAll('.entity-cb-item');
            items.forEach(item => {
                const text = item.innerText.toLowerCase();
                item.style.display = text.includes(term) ? 'flex' : 'none';
            });
        };

        const openGroupModal = () => {
            document.getElementById('group-modal-title').innerText = 'Создать группу';
            document.getElementById('group-name-input').value = '';
            document.getElementById('group-original-name').value = '';
            document.getElementById('entity-search-input').value = '';
            renderEntitiesListForModal([]);
            document.getElementById('group-modal').classList.remove('hidden');
        };

        const editGroup = (name) => {
            const groups = getParsedGroups();
            document.getElementById('group-modal-title').innerText = 'Изменить группу';
            document.getElementById('group-name-input').value = name;
            document.getElementById('group-original-name').value = name;
            document.getElementById('entity-search-input').value = '';
            renderEntitiesListForModal(groups[name] || []);
            document.getElementById('group-modal').classList.remove('hidden');
        };

        const closeGroupModal = () => {
            document.getElementById('group-modal').classList.add('hidden');
        };

        const saveGroup = async () => {
            const name = document.getElementById('group-name-input').value.trim();
            if (!name) {
                alert('Введите название группы');
                return;
            }

            const origName = document.getElementById('group-original-name').value;
            const selected = Array.from(document.querySelectorAll('.entity-checkbox:checked')).map(cb => cb.value);

            const groups = getParsedGroups();
            if (origName && origName !== name) {
                delete groups[origName];
            }
            groups[name] = selected;

            const configData = { ...state.config, tg_groups: JSON.stringify(groups) };

            try {
                const res = await fetch(\`/api/plugins/\${state.plugin_id}/config\`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ config: configData })
                });
                if (res.ok) {
                    state.config.tg_groups = JSON.stringify(groups);
                    renderCustomGroups();
                    closeGroupModal();
                    showMessage('success-banner', 'Группа сохранена');
                } else {
                    alert('Ошибка сохранения группы');
                }
            } catch (err) {
                alert(err.message);
            }
        };

        const deleteGroup = async (name) => {
            if (!confirm(\`Удалить группу "\${name}"?\`)) return;

            const groups = getParsedGroups();
            delete groups[name];

            const configData = { ...state.config, tg_groups: JSON.stringify(groups) };
            try {
                const res = await fetch(\`/api/plugins/\${state.plugin_id}/config\`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ config: configData })
                });
                if (res.ok) {
                    state.config.tg_groups = JSON.stringify(groups);
                    renderCustomGroups();
                    showMessage('success-banner', 'Группа удалена');
                } else {
                    alert('Ошибка удаления группы');
                }
            } catch (err) {
                alert(err.message);
            }
        };

        const renderEntities = () => {
`;

html = html.replace(/const renderEntities = \(\) => {/, jsAdditions);

html = html.replace(/if \(tab === 'groups'\) {[\s\S]*?}/, `if (tab === 'groups') {
                document.getElementById('content-groups').classList.remove('hidden');
                document.getElementById('tab-groups').className = 'px-4 py-2 border-b-2 font-medium text-sm text-blue-600 border-blue-600';
                loadConfigForGroups();
            }`);


html = html.replace(/const init = async \(\) => {[\s\S]*?await fetchStatus\(\);/, `const init = async () => {
            const res = await fetch(\`\${basePath}/meta\`);
            const meta = await res.json();
            state.plugin_id = meta.plugin_id;

            await loadConfigForGroups();
            await fetchStatus();`);

fs.writeFileSync('plugins/home_assistant/web/index.html', html);
