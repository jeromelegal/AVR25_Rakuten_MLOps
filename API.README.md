# API Gateway - Documentation Technique

L'API Gateway sert de point d'entrée pour les clients qui interagissent avec nos services backend. Il centralise l'authentification, le logging, et le routage des requêtes vers les services appropriés comme MongoDB et PostgreSQL. Cette documentation se concentre sur la structure du code, les fonctionnalités principales, et l'architecture logicielle.

## Structure du Projet

Le projet est organisé en modules, chacun ayant une responsabilité distincte pour maintenir une séparation claire des préoccupations. Voici un aperçu de la structure du projet :

- `main.py`: Point d'entrée de l'application, où l'application FastAPI est configurée et lancée.
- `config/`: Dossier contenant la configuration de l'application, notamment les paramètres et les variables d'environnement.
- `api/`: Contient tous les modules et sous-dossiers relatifs à la logique métier, aux middlewares, aux routes et à l'authentification.

## Modules Principaux

### 1. Configuration et Initialisation

Le fichier `main.py` est le point d'entrée de l'application. Il initialise FastAPI, configure le middleware, et enregistre les routes.

```python
def create_app(settings: Settings):
    app = FastAPI()
    app.state.settings = settings
    app.add_middleware(CORSMiddleware, ...)
    app.add_middleware(LoggingMiddleware)
    auth_middleware = create_auth_middleware(settings)
    app.add_middleware(auth_middleware)
    app.include_router(login_router, ...)
    # Autres configurations...
    return app
```

### 2. Middlewares

#### LoggingMiddleware

Ce middleware est responsable de l'enregistrement des détails des requêtes et réponses, ce qui est crucial pour le débogage et la surveillance. Il enregistre la méthode, l'URL, les en-têtes, le corps de la requête, le code de statut de la réponse, et le temps de traitement.

```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        # D'autres fonctionnalités de logging...
        response = await call_next(request)
        logger.info(f"Response Status: {response.status_code}")
        return response
```

#### AuthMiddleware

Il vérifie l'authenticité des requêtes, en particulier pour les endpoints protégés. Il vérifie le token JWT dans l'en-tête d'autorisation et assure que seules les requêtes légitimes sont traitées.

```python
def create_auth_middleware(settings: Settings) -> DispatchFunction:
    class AuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if PUBLIC_ENDPOINTS.get((request.method, request.url.path)):
                return await call_next(request)
            # Vérification des headers, token JWT, etc.
            response = await call_next(request)
            return response
    return AuthMiddleware
```

### 3. Gestion des Clients

Une des forces de l'API Gateway est sa capacité à interagir de manière générique avec différents services de stockage. Grâce à une approche modulaire, chaque client (comme `MongoDBClient` ou `PostgreSQLClient`) implémente une interface commune pour des opérations CRUD. Cela permet aux développeurs de se concentrer sur la mise en place de nouvelles routes, sans avoir à se soucier des détails spécifiques à chaque service de stockage.

#### Conception Modulaire des Clients

L'API Gateway est conçu pour interagir avec des services backend de manière générique grâce à une approche modulaire. Chaque client de base de données est implémenté comme un module indépendant qui respecte une interface commune. Cela permet d'ajouter de nouveaux types de clients sans modifier le code existant.

##### ClientManager

Le `ClientManager` est responsable de l'initialisation et de la gestion des clients pour les différentes bases de données.

```python
class ClientManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        self.register_client("mongodb", MongoDBClient(self.settings))
        self.register_client("postgresql", PostgreSQLClient(self.settings))

    def register_client(self, name: str, client):
        self.clients[name] = client

    def get_client(self, name: str):
        client = self.clients.get(name)
        if not client:
            raise ValueError(f"Client '{name}' not found.")
        return client
```

##### Clients de Base de Données

Chaque client implémente des méthodes pour réaliser des opérations CRUD sur sa base de données respective. Par exemple, le `MongoDBClient` et le `PostgreSQLClient` partagent une interface commune :

```python
class MongoDBClient:
    def create_entity(self, token: str, collection: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation spécifique à MongoDB
        pass

    def read_entity(self, token: str, collection: str, entity_id: str) -> Dict[str, Any]:
        # Implémentation spécifique à MongoDB
        pass

class PostgreSQLClient:
    def create_entity(self, token: str, table: str, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation spécifique à PostgreSQL
        pass

    def read_entity(self, token: str, table: str, entity_id: str) -> Dict[str, Any]:
        # Implémentation spécifique à PostgreSQL
        pass
```

Cette approche permet non seulement d'ajouter facilement de nouveaux clients pour des services supplémentaires, mais garantit également une cohérence dans la manière dont ces services sont utilisés dans le reste de l'application.

Grâce à cette généricité, les développeurs peuvent concentrer leurs efforts sur la mise en place de nouvelles routes, qui auront un impact sur les différents objets gérés par les clients. Par exemple, on peut facilement ajouter une route pour gérer de nouvelles opérations sur des utilisateurs ou d'autres entités, sans se soucier de la manière dont ces opérations sont réalisées pour chaque type de base de données.

### 4. Authentification

Le module d'authentification gère les processus de connexion, d'inscription et de suppression des utilisateurs. Les contrôleurs (routes) utilisent des services comme `BackendAuthenticator` pour gérer les opérations d'authentification.

```python
class BackendAuthenticator:
    def authenticate(self, credentials: Dict[str, str]) -> Tuple[Dict, Dict, Dict]:
        backend_tokens = {}
        backend_uid = {}
        concat_uid = ""
        for client in self.clients:
            auth_data = client.authenticate(token=None, credentials=credentials)
            if auth_data:
                user_id, token = auth_data.get("user_id"), auth_data.get("access_token")
                backend_tokens[client.name] = token
                backend_uid[client.name] = user_id
                concat_uid += f"_{user_id}"
        return ({"user_id": concat_uid}, backend_tokens, backend_uid)
```

### 5. Routes et Points de Terminaison

Les routes sont définies dans le dossier `api/routes/` et sont utilisées pour gérer les requêtes HTTP. Chaque fichier de route définit un ensemble d'endpoints relatifs à une fonctionnalité spécifique, comme l'authentification, l'inscription, ou la suppression d'utilisateur.

#### Exemples de Routes

Voici un exemple de mise en place d'une route pour l'inscription d'un utilisateur, exploitant la généricité des clients :

```python
@router.post("/signup")
async def signup(
    request: Request,
    user: UserSignup,
    client_manager: ClientManager = Depends(get_client_manager)
):
    try:
        mongodb_client = client_manager.get_client("mongodb")
        postgresql_client = client_manager.get_client("postgresql")
        user_data = {
            "username": user.username,
            "email": user.email,
            "password": user.password
        }
        # Créez l'utilisateur dans MongoDB et PostgreSQL
        mongodb_response = mongodb_client.create_entity(token=None, collection="user", entity_data=user_data)
        postgresql_response = postgresql_client.create_entity(token=None, table="user", entity_data=user_data)
        if mongodb_response and postgresql_response:
            return {"message": "User created successfully"}
        else:
            # Rollback si échec
            rollback_operations(mongodb_client, postgresql_client, mongodb_response, postgresql_response)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in one of the databases"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup error: {str(e)}"
        )
```

### 6. Tests

Le projet inclut des tests pour garantir la fiabilité des fonctionnalités. Les tests utilisent `pytest` pour simuler les requêtes et vérifier les réponses. Les tests incluent des scénarios de base comme l'inscription et la connexion des utilisateurs, ainsi que leur suppression.

```python
def test_delete_user_flow():
    signup_response = client.post("/signup", json={...})
    assert signup_response.status_code == 200
    login_response = client.post("/login", data={...})
    assert login_response.status_code == 200
    # Vérification de la suppression d'utilisateur...
```

## Conclusion

L'API Gateway est conçue pour être modulaire, sécurisée et facile à étendre. Chaque composant (middleware, client manager, authentification) est conçu pour être indépendant, permettant ainsi une maintenance et une extension simplifiées.

Pour contribuer ou étendre cette API, il est recommandé de se familiariser avec FastAPI et les principes de conception des middleware. Chaque module peut être testé individuellement, et les nouveaux services peuvent être ajoutés en étendant le `ClientManager`.
