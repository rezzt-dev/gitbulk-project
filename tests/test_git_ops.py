"""
tests/test_git_ops.py

Suite de pruebas para src/model/git_ops.py.
Verifica la lógica de operaciones Git mockeando el objeto Repo de GitPython
para no requerir repositorios Git reales durante la ejecución de los tests.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model.git_ops import run_git_operation, get_repo_metadata, get_all_branches, clone_repo


def _make_mock_repo(
    is_dirty=False,
    active_branch_name="main",
    tracking_branch_name=None,
    commits_behind=0,
    commits_ahead=0,
    has_remotes=True,
    is_detached=False,
):
    """
    Construye un mock del objeto git.Repo con la configuración indicada,
    evitando la creación de repositorios reales en el sistema de ficheros.
    """
    repo = MagicMock()
    repo.is_dirty.return_value = is_dirty
    repo.head.is_detached = is_detached

    branch = MagicMock()
    branch.name = active_branch_name

    if tracking_branch_name:
        tracking = MagicMock()
        tracking.name = tracking_branch_name
        branch.tracking_branch.return_value = tracking
        repo.iter_commits.side_effect = lambda ref: (
            [MagicMock()] * commits_behind if f"{active_branch_name}..{tracking_branch_name}" in ref
            else [MagicMock()] * commits_ahead
        )
    else:
        branch.tracking_branch.return_value = None

    repo.active_branch = branch

    remote = MagicMock()
    remote.name = "origin"
    remote.urls = iter(["https://github.com/org/repo.git"])
    repo.remotes = [remote] if has_remotes else []

    return repo


class TestRunGitOperationStatus(unittest.TestCase):

    def _run(self, repo_mock, path="/fake/repo"):
        with patch("model.git_ops.os.path.exists", return_value=True), \
             patch("model.git_ops.Repo", return_value=repo_mock):
            return run_git_operation(path, "status")

    def test_status_clean(self):
        """Un repo sin cambios y al día con el remoto debe devolver CLEAN."""
        repo = _make_mock_repo(is_dirty=False)
        repo.iter_commits.side_effect = lambda ref: []
        status, detail, _, _ = self._run(repo)
        self.assertEqual(status, "CLEAN")

    def test_status_modified(self):
        """Un repo con cambios sin confirmar debe devolver MODIFIED."""
        repo = _make_mock_repo(is_dirty=True)
        repo.untracked_files = ["file.txt"]
        repo.index.diff.return_value = []
        status, _, _, _ = self._run(repo)
        self.assertEqual(status, "MODIFIED")

    def test_status_behind(self):
        """Un repo más atrás que el remoto debe devolver BEHIND."""
        repo = _make_mock_repo(tracking_branch_name="origin/main", commits_behind=3)
        repo.iter_commits.side_effect = lambda ref: (
            [MagicMock()] * 3 if "main..origin/main" in ref else []
        )
        status, detail, _, _ = self._run(repo)
        self.assertEqual(status, "BEHIND")
        self.assertEqual(detail, "3")

    def test_status_ahead(self):
        """Un repo por delante del remoto debe devolver AHEAD."""
        repo = _make_mock_repo(tracking_branch_name="origin/main")
        repo.iter_commits.side_effect = lambda ref: (
            [] if "main..origin/main" in ref else [MagicMock(), MagicMock()]
        )
        status, detail, _, _ = self._run(repo)
        self.assertEqual(status, "AHEAD")

    def test_directorio_sin_git_devuelve_error(self):
        """Si .git no existe en la ruta, debe devolver ERROR sin lanzar excepción."""
        with patch("model.git_ops.os.path.exists", return_value=False):
            status, _, _, _ = run_git_operation("/ruta/falsa", "status")
        self.assertEqual(status, "ERROR")


class TestRunGitOperationCheckout(unittest.TestCase):

    def _run(self, repo_mock, branch, path="/fake/repo"):
        with patch("model.git_ops.os.path.exists", return_value=True), \
             patch("model.git_ops.Repo", return_value=repo_mock):
            return run_git_operation(path, "checkout", target_branch=branch)

    def test_checkout_ya_en_la_rama(self):
        """Si ya está en la rama destino, debe devolver CLEAN."""
        repo = _make_mock_repo(active_branch_name="main")
        repo.head.is_detached = False
        status, detail, _, _ = self._run(repo, "main")
        self.assertEqual(status, "CLEAN")

    def test_checkout_rama_inexistente_devuelve_ignored(self):
        """Si la rama no existe local ni remotamente, debe devolver IGNORED."""
        repo = _make_mock_repo(active_branch_name="main")
        repo.head.is_detached = False
        repo.heads = []
        repo.remotes = []
        status, _, _, _ = self._run(repo, "feature/inexistente")
        self.assertEqual(status, "IGNORED")

    def test_checkout_sin_branch_devuelve_error(self):
        """Si no se pasa target_branch, debe devolver ERROR."""
        repo = _make_mock_repo()
        with patch("model.git_ops.os.path.exists", return_value=True), \
             patch("model.git_ops.Repo", return_value=repo):
            status, _, _, _ = run_git_operation("/fake/repo", "checkout", target_branch=None)
        self.assertEqual(status, "ERROR")


class TestGetRepoMetadata(unittest.TestCase):

    def test_devuelve_url_y_rama(self):
        """Debe extraer correctamente la URL remota y la rama activa."""
        repo = _make_mock_repo(active_branch_name="develop")
        with patch("model.git_ops.os.path.exists", return_value=True), \
             patch("model.git_ops.Repo", return_value=repo):
            metadata = get_repo_metadata("/fake/repo")
        self.assertIn("github.com", metadata["url"])
        self.assertEqual(metadata["branch"], "develop")
        self.assertEqual(metadata["error"], "")

    def test_error_en_campo_error_si_repo_invalido(self):
        """Si el repositorio es inválido, el campo 'error' debe estar poblado."""
        from git import exc
        with patch("model.git_ops.Repo", side_effect=exc.InvalidGitRepositoryError):
            metadata = get_repo_metadata("/ruta/invalida")
        self.assertNotEqual(metadata["error"], "")


class TestGetAllBranches(unittest.TestCase):

    def test_lista_ramas_locales_y_remotas(self):
        """Debe devolver las ramas locales y las que solo existen en remoto."""
        repo = MagicMock()
        repo.head.is_detached = False
        local_branch = MagicMock()
        local_branch.name = "main"
        repo.active_branch = local_branch
        repo.heads = [local_branch]

        remote = MagicMock()
        ref_main = MagicMock()
        ref_main.remote_head = "main"
        ref_feature = MagicMock()
        ref_feature.remote_head = "feature/nueva"
        remote.refs = [ref_main, ref_feature]
        remote.name = "origin"
        repo.remotes = [remote]

        with patch("model.git_ops.Repo", return_value=repo):
            data = get_all_branches("/fake/repo")

        self.assertEqual(data["current"], "main")
        self.assertIn("main", data["local"])
        self.assertIn("origin/feature/nueva", data["remote_only"])
        self.assertEqual(data["error"], "")


if __name__ == "__main__":
    unittest.main()
