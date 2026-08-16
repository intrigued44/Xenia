features = [
    'startVoiceCapture', 'handleCanvasDrop', 'handleSidebarDragStart',
    'nodes_json', 'voice-modal', 'drag-over', 'voice-pulse',
    'loadAutoIntoCanvas', 'deleteAuto', 'confirmDeleteAuto',
    'loadMyAutomations', 'saveAndRunFlow', 'generateFlowScript',
    'makeDraggableItem', 'buildFlowFromVoice', 'renderFlowCanvas',
    'openNodeConfig', 'saveNodeConfig', 'insertConditionNode',
    'removeNode', 'clearFlowCanvas', 'addTriggerNode', 'addActionNode'
]

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'ui', 'index.html'), encoding='utf-8') as f:
    html = f.read()

print(f"Total chars: {len(html):,}")
print("Feature check:")
for feat in features:
    status = "OK" if feat in html else "MISSING"
    print(f"  {status}: {feat}")
