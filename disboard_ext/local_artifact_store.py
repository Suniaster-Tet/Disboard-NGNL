"""Built-in local artifact storage plugin."""
from disboard_artifacts import LocalArtifactStore


class LocalArtifactStorePlugin:
    def run(self, root, action, *args, **kwargs):
        store = LocalArtifactStore(root)
        operation = getattr(store, action, None)
        if action.startswith("_") or not callable(operation):
            raise ValueError(f"Acción de almacenamiento no permitida: {action}")
        return operation(*args, **kwargs)


def create_plugin():
    return LocalArtifactStorePlugin()
