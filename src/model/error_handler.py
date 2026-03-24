import re
from git import exc

def parse_git_error(e: exc.GitCommandError) -> str:
    """
    Parsea y limpia los errores crudos devueltos por GitPython,
    traduciendo los más comunes a mensajes limpios y amigables para la UI.
    Si el error es desconocido, lo trunca para evitar romper visualmente la consola.
    """
    error_msg = e.stderr.strip() if e.stderr else str(e)
    if not error_msg:
        return "Error desconocido en operación Git."

    # 1. Errores de Red / SSH / Accesibilidad
    if "Could not resolve host" in error_msg or "Connection timed out" in error_msg or "Could not read from remote repository" in error_msg:
        return "Error de red: El repositorio remoto no es accesible o la conexión falló."
    
    if "Connection refused" in error_msg:
        return "Error de red: Conexión rechazada por el servidor de origen."

    if "Repository not found" in error_msg:
        return "Error 404: Repositorio no encontrado en el origen remoto."

    # 2. Errores de Autenticación
    if "Permission denied" in error_msg or "Authentication failed" in error_msg or "could not read Username" in error_msg:
        return "Error de Autenticación: Credenciales SSH/HTTPS inválidas o faltantes."

    # 3. Errores de Merge y Conflictos
    if "Applied autostash" in error_msg and "CONFLICT" in error_msg.upper():
        return "Conflicto de Autostash: Los cambios descargados chocan con los locales. Resolución manual requerida."
        
    if "overwritten by merge" in error_msg or "Please commit your changes or stash them" in error_msg:
        return "Conflicto de pull: Cambios locales sin guardar impiden la actualización de la red."
        
    if "Not possible to fast-forward" in error_msg or "divergent branches" in error_msg or "Need to specify how to reconcile" in error_msg:
        return "Ramas divergentes: El entorno remoto local y red han avanzado en direcciones distintas."

    # 4. Clone errors
    if "already exists and is not an empty directory" in error_msg or "already exists" in error_msg:
        return "Conflicto de sistema: El directorio destino ya existe o no está vacío."

    # 5. Fallback por defecto: truncar errores incomprensiblemente largos
    lines = [line.strip() for line in error_msg.split('\n') if line.strip()]
    if len(lines) > 3:
        return '\n    '.join(lines[:3]) + "\n    [...] Error Git nativo truncado."
        
    return '\n    '.join(lines)
