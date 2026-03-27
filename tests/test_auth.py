"""
tests/test_auth.py

Suite de pruebas para src/model/auth.py.
Verifica el almacenamiento, deduplicación y extracción del PAT de GitHub.
Todos los tests trabajan sobre archivos temporales para no alterar el sistema real.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model.auth import setup_global_git_credentials, get_github_token


class TestSetupGlobalGitCredentials(unittest.TestCase):

    def setUp(self):
        """Redirige el fichero de credenciales a una ruta temporal segura."""
        self.tmp_dir = tempfile.mkdtemp(prefix="gitbulk_auth_test_")
        self.fake_credentials_file = Path(self.tmp_dir) / ".git-credentials"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _run_setup(self, username="testuser", token="ghp_faketoken123"):
        """Helper que ejecuta setup parchando Path.home() y subprocess."""
        with patch("model.auth.Path.home", return_value=Path(self.tmp_dir)), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            return setup_global_git_credentials(username, token)

    def test_guarda_credenciales_en_fichero(self):
        """El fichero de credenciales debe crearse con la entrada correcta."""
        result = self._run_setup("usuario1", "token_abc")
        self.assertTrue(result)
        self.assertTrue(self.fake_credentials_file.exists())
        content = self.fake_credentials_file.read_text(encoding="utf-8")
        self.assertIn("https://usuario1:token_abc@github.com", content)

    def test_reemplaza_credencial_github_existente(self):
        """Si ya existe una entrada de github.com, debe reemplazarse, no duplicarse."""
        self.fake_credentials_file.write_text(
            "https://usuario_viejo:token_viejo@github.com\n", encoding="utf-8"
        )
        self._run_setup("usuario_nuevo", "token_nuevo")
        content = self.fake_credentials_file.read_text(encoding="utf-8")
        self.assertIn("usuario_nuevo:token_nuevo", content)
        self.assertNotIn("usuario_viejo", content)
        # Solo debe haber una línea de github.com
        github_lines = [l for l in content.splitlines() if "@github.com" in l]
        self.assertEqual(len(github_lines), 1)

    def test_preserva_otras_credenciales(self):
        """Las credenciales de otros servidores no deben ser borradas."""
        self.fake_credentials_file.write_text(
            "https://user:pass@gitlab.com\n", encoding="utf-8"
        )
        self._run_setup("nuevo", "token")
        content = self.fake_credentials_file.read_text(encoding="utf-8")
        self.assertIn("https://user:pass@gitlab.com", content)
        self.assertIn("@github.com", content)

    def test_devuelve_false_si_subprocess_falla(self):
        """Debe devolver False si el helper git config falla."""
        import subprocess
        with patch("model.auth.Path.home", return_value=Path(self.tmp_dir)), \
             patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = setup_global_git_credentials("u", "t")
        self.assertFalse(result)


class TestGetGithubToken(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="gitbulk_token_test_")
        self.fake_credentials_file = Path(self.tmp_dir) / ".git-credentials"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_extrae_token_correctamente(self):
        """Debe extraer el token de una línea de credenciales válida."""
        self.fake_credentials_file.write_text(
            "https://myuser:ghp_secret_token@github.com\n", encoding="utf-8"
        )
        with patch("model.auth.Path.home", return_value=Path(self.tmp_dir)):
            token = get_github_token()
        self.assertEqual(token, "ghp_secret_token")

    def test_devuelve_none_si_fichero_no_existe(self):
        """Debe devolver None si el fichero de credenciales no existe."""
        with patch("model.auth.Path.home", return_value=Path(self.tmp_dir)):
            token = get_github_token()
        self.assertIsNone(token)

    def test_devuelve_none_si_no_hay_entrada_github(self):
        """Debe devolver None si el fichero existe pero no contiene github.com."""
        self.fake_credentials_file.write_text(
            "https://user:pass@gitlab.com\n", encoding="utf-8"
        )
        with patch("model.auth.Path.home", return_value=Path(self.tmp_dir)):
            token = get_github_token()
        self.assertIsNone(token)


if __name__ == "__main__":
    unittest.main()
