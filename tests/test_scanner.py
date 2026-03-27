"""
tests/test_scanner.py

Suite de pruebas para src/model/scanner.py.
Verifica el descubrimiento recursivo de repositorios Git y los casos límite.
"""

import os
import sys
import unittest
import tempfile
import shutil

# Permite ejecutar estas pruebas desde la raiz del proyecto sin instalar el paquete.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model.scanner import find_git_repos


def _make_git_repo(base_dir: str, name: str) -> str:
    """Crea un directorio con un subdirectorio .git simulado."""
    repo_path = os.path.join(base_dir, name)
    os.makedirs(os.path.join(repo_path, ".git"), exist_ok=True)
    return repo_path


class TestFindGitRepos(unittest.TestCase):

    def setUp(self):
        """Crea un workspace temporal limpio para cada prueba."""
        self.workspace = tempfile.mkdtemp(prefix="gitbulk_test_")

    def tearDown(self):
        """Elimina el workspace temporal al finalizar cada prueba."""
        shutil.rmtree(self.workspace, ignore_errors=True)

    def test_ruta_inexistente_devuelve_lista_vacia(self):
        """Si la ruta raíz no existe, debe devolver una lista vacía."""
        results = find_git_repos("/ruta/que/no/existe/en/el/sistema")
        self.assertEqual(results, [])

    def test_directorio_vacio_devuelve_lista_vacia(self):
        """Un directorio real pero sin repositorios no debe devolver nada."""
        results = find_git_repos(self.workspace)
        self.assertEqual(results, [])

    def test_descubre_un_repositorio_simple(self):
        """Debe encontrar un único repositorio en el directorio raíz."""
        repo = _make_git_repo(self.workspace, "mi-repo")
        results = find_git_repos(self.workspace)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], repo)

    def test_descubre_multiples_repositorios_al_mismo_nivel(self):
        """Debe encontrar todos los repositorios al mismo nivel de profundidad."""
        repos = [_make_git_repo(self.workspace, f"repo-{i}") for i in range(5)]
        results = find_git_repos(self.workspace)
        self.assertCountEqual(results, repos)

    def test_no_desciende_dentro_de_un_repositorio(self):
        """
        Si un repositorio tiene subdirectorios con sus propios .git,
        el scanner no debe descender dentro del padre (comportamiento de dirs[:] = []).
        Solo debe devolver el repositorio padre.
        """
        parent_repo = _make_git_repo(self.workspace, "parent")
        # Crear un repo anidado dentro del padre (simula un submódulo)
        _make_git_repo(parent_repo, "submodule")
        results = find_git_repos(self.workspace)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], parent_repo)

    def test_descubre_repositorios_en_subdirectorios(self):
        """Debe encontrar repositorios anidados dentro de subdirectorios normales."""
        subdir = os.path.join(self.workspace, "proyectos", "backend")
        os.makedirs(subdir, exist_ok=True)
        repo = _make_git_repo(subdir, "api-service")
        results = find_git_repos(self.workspace)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], repo)


if __name__ == "__main__":
    unittest.main()
