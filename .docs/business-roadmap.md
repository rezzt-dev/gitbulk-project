## GITBULK | BUSINESS ROADMAP
> Roadmap completo de la actualización del proyecto para la adaptación en un entorno de empresa
BUSINESS ROADMAP
---
### BUSINESS ROADMAP | INFORMACIÓN GENERAL
En base a la visión de gestionar aplicaciones distribuidas ("órganos" en diferentes repositorios) bajo un esquema de actualización centralizada, GitBulk ya cuenta con una base muy sólida.

Sin embargo, para que sea un orquestador definitivo en entornos corporativos (alta rotación de repos, altas y bajas en microservicios) existe un camino de evolución claro.

---
### BUSINESS ROADMAP | FASE 1: LO QUE YA ESTÁ IMPLEMENTADO
Actualmente GitBulk tiene los pilares fundamentales, pero pueden ser refinados para la experiencia empresarial:

#### 1. Gestión Concurrente
- **Implementado:** Un sistema robusto de hilos (hasta 50 simultáneos) que manda los comandos fetch, pull, status a Git en paralelo.
- **Mejorable:** Añadir gestión dinámica de recursos. En discos duros antiguos (HDD), acceder a 50 repositorios a la vez puede crear un cuello de botella. Se debería incluir una detección del tipo de disco o agrupar las peticiones inteligentemente.

#### 2. Snapshots y Grupos
- **Implementado:** Los comandos export (que lee qué repositorios tienes y crea un archivo JSON) y restore (que lee el JSON y clona todos los repos que te falten). Esto es ideal para que un empleado nuevo monte todo su ecosistema con un solo comando.
- **Mejorable:** Evolucionar de un simple archivo snapshot.json a un sistema de Workspaces/Espacios de Trabajo. Es decir, que el programa te permita guardar configuraciones con nombre (gitbulk workspace load eac-center), sin tener que andar buscando el archivo JSON.

#### 3. Autenticación Centralizada
- **Implementado:** El comando auth que gestiona de manera centralizada el token (PAT) de GitHub/GitLab para evitar que cada repositorio pida la contraseña al actualizar masivamente.
- **Mejorable:** Soporte más robusto para Agent SSH. Muchas empresas descartan el usuario/contraseña (incluso tokens) a favor de claves SSH. Asegurar que GitBulk orquesta sin problemas con el gestor SSH del sistema operativo (Pageant en Windows o ssh-agent en Linux).

---
### BUSINESS ROADMAP | FASE 2: ROADMAP HACIA EL ORQUESTADOR EMPRESARIAL COMPLETO
Para cubrir esa casuística que mencionas (empresas que descontinúan repos, añaden nuevos y el engorro de bash), GitBulk debe implementar las siguientes capacidades:

#### 1. El concepto de "Grupos" o "Tags"
- **Implementación:** Permite definir un archivo global (por ejemplo .gitbulk.yaml) en la carpeta base donde se asignan etiquetas a las rutas.
- **Comando esperado:** gitbulk pull --group backend

#### 2. Sincronización Destructiva Segura
Esto resuelve exactamente ese punto. Si la empresa deprecia el repositorio `Auth-v1` y añade `Auth-v2`, el desarrollador no debería tener que buscar en su explorador de archivos para borrar el viejo.
- **Implementación:** Un nuevo comando sync en lugar de solo restore. Este comando compara tu carpeta local con el "JSON oficial" proporcionado por la empresa.
- **Flujo:**
  - GitBulk ve que en tu carpeta está Auth-v1 pero ya no en el listado oficial.
  - Aviso: "El repositorio Auth-v1 ha sido descontinuado. ¿Deseas archivarlo o eliminarlo localmente?".
  - GitBulk clona automáticamente Auth-v2.


#### 3. Operaciones de Subida Masiva
Actualmente es muy fuerte leyendo datos (status, fetch, pull), pero para ser completo necesita empujar código también con precaución.
- **Implementaciones clave:**
  - `gitbulk commit -m "update libs"`: Commitea automáticamente en todos los repositorios que tengan cambios de una misma rama.
  - `gitbulk push`: Empuja los cambios al remoto masivamente.

#### 4. Integración Directa con la API de Forgejo / GitLab
Actualmente GitBulk habla con Git local, lo que asegura compatibilidad universal. Pero un paso extra muy valorado por las empresas sería hablar con las plataformas.
- **Por qué:** Para crear "Pull Requests" de forma masiva en varios repos de golpe (un dolor de cabeza corporativo muy común cuando hay que actualizar la versión de una dependencia en 20 microservicios).
- **Implementación:** Módulos específicos en Python que interactúen mediante API REST (ya cuenta con un sistema inicial mediante ci-status).

#### 5. Consola Interactiva para Conflictos
Cuando lanzas un pull de 20 repositorios, es común que 2 tengan conflictos (cambios locales sin guardar).
- **Mejora:** En lugar de simplemente abortar la operación para esos repositorios arrojando un error en texto rojo (como hace ahora), ofrecer una terminal guiada paso a paso que te diga "Conflicto en Repositorio C. ¿Quieres hacer un stash, sobrescribir o ignorar?", resolverlo ahí mismo y continuar con el lote.
---