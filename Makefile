# Configuración del proyecto 2FA Biométrico
IMAGE_NAME := 2fa-biometric-app
CONTAINER_NAME := 2fa-app
VOLUME_NAME := 2fa-data
PORT := 5001

# ================================================================
# CONSTRUCCIÓN
# ================================================================

.PHONY: build
build:
	@echo "🔨 Construyendo imagen Docker..."
	docker build -t $(IMAGE_NAME) .
	@echo "✅ Imagen construida: $(IMAGE_NAME)"

.PHONY: rebuild
rebuild: clean build
	@echo "✅ Imagen reconstruida desde cero"

# ================================================================
# GESTIÓN DE VOLÚMENES
# ================================================================

.PHONY: volume-create
volume-create:
	@echo "📦 Creando volumen para datos persistentes..."
	docker volume create $(VOLUME_NAME)
	@echo "✅ Volumen creado: $(VOLUME_NAME)"

.PHONY: volume-inspect
volume-inspect:
	@echo "🔍 Información del volumen:"
	docker volume inspect $(VOLUME_NAME)

.PHONY: volume-backup
volume-backup:
	@echo "💾 Creando backup del volumen..."
	docker run --rm -v $(VOLUME_NAME):/data -v $(PWD):/backup alpine tar czf /backup/2fa-backup-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "✅ Backup creado en $(PWD)"

.PHONY: volume-restore
volume-restore:
	@echo "⚠️  Restaurando último backup..."
	@if [ -z "$$(ls -t 2fa-backup-*.tar.gz 2>/dev/null | head -1)" ]; then \
		echo "❌ No se encontró ningún backup"; \
		exit 1; \
	fi
	docker run --rm -v $(VOLUME_NAME):/data -v $(PWD):/backup alpine tar xzf /backup/$$(ls -t 2fa-backup-*.tar.gz | head -1) -C /data
	@echo "✅ Backup restaurado"

# ================================================================
# EJECUCIÓN
# ================================================================

.PHONY: run
run: volume-create
	@echo "🚀 Iniciando contenedor con persistencia..."
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-v $(VOLUME_NAME):/app/data \
		$(IMAGE_NAME)
	@echo "✅ Contenedor iniciado en http://localhost:$(PORT)"
	@echo "📊 Ver logs con: make logs"

.PHONY: run-it
run-it: volume-create
	@echo "🚀 Iniciando contenedor en modo interactivo..."
	docker run -it --rm \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-v $(VOLUME_NAME):/app/data \
		$(IMAGE_NAME)

.PHONY: run-dev
run-dev:
	@echo "🔧 Iniciando contenedor en modo desarrollo (sin volumen)..."
	docker run -it --rm \
		--name $(CONTAINER_NAME)-dev \
		-p $(PORT):$(PORT) \
		-v $(PWD):/app \
		$(IMAGE_NAME)

# ================================================================
# GESTIÓN DE CONTENEDORES
# ================================================================

.PHONY: start
start:
	@echo "▶️  Iniciando contenedor..."
	docker start $(CONTAINER_NAME)
	@echo "✅ Contenedor iniciado"

.PHONY: stop
stop:
	@echo "⏸️  Deteniendo contenedor..."
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@echo "✅ Contenedor detenido"

.PHONY: restart
restart: stop start
	@echo "✅ Contenedor reiniciado"

.PHONY: logs
logs:
	@echo "📋 Mostrando logs del contenedor..."
	docker logs -f $(CONTAINER_NAME)

.PHONY: logs-tail
logs-tail:
	@echo "📋 Últimas 50 líneas de logs..."
	docker logs --tail 50 $(CONTAINER_NAME)

.PHONY: shell
shell:
	@echo "🐚 Abriendo shell en el contenedor..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

.PHONY: status
status:
	@echo "📊 Estado de contenedores:"
	@docker ps -a --filter name=$(CONTAINER_NAME)
	@echo ""
	@echo "📦 Volúmenes:"
	@docker volume ls --filter name=$(VOLUME_NAME)

# ================================================================
# LIMPIEZA
# ================================================================

.PHONY: clean
clean: stop
	@echo "🧹 Limpiando contenedores..."
	docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	docker rm -f $$(docker ps -aq --filter ancestor=$(IMAGE_NAME)) 2>/dev/null || true
	@echo "✅ Contenedores eliminados"

.PHONY: clean-all
clean-all: clean
	@echo "🧹 Eliminando imagen..."
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@echo "✅ Imagen eliminada"

.PHONY: clean-volume
clean-volume:
	@echo "⚠️  ¿Estás seguro de eliminar el volumen con TODOS los datos? [y/N] " && read ans && [ $${ans:-N} = y ]
	docker volume rm $(VOLUME_NAME)
	@echo "✅ Volumen eliminado"

.PHONY: prune
prune:
	@echo "🧹 Limpiando recursos Docker no utilizados..."
	docker system prune -f
	@echo "✅ Limpieza completada"

# ================================================================
# UTILIDADES
# ================================================================

.PHONY: ps
ps:
	@docker ps --filter name=$(CONTAINER_NAME)

.PHONY: inspect
inspect:
	@echo "🔍 Información del contenedor:"
	docker inspect $(CONTAINER_NAME)

.PHONY: stats
stats:
	@echo "📊 Estadísticas en tiempo real:"
	docker stats $(CONTAINER_NAME)

.PHONY: db-shell
db-shell:
	@echo "💾 Accediendo a la base de datos..."
	docker exec -it $(CONTAINER_NAME) sqlite3 /app/data/users_2fa.db

# ================================================================
# DESARROLLO
# ================================================================

.PHONY: test
test:
	@echo "🧪 Ejecutando tests..."
	docker run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		python -m pytest tests/ -v

.PHONY: lint
lint:
	@echo "🔍 Ejecutando linter..."
	docker run --rm \
		-v $(PWD):/app \
		$(IMAGE_NAME) \
		python -m pylint *.py

# ================================================================
# AYUDA
# ================================================================

.PHONY: help
help:
	@echo "=================================="
	@echo "  Sistema 2FA Biométrico - Docker"
	@echo "=================================="
	@echo ""
	@echo "📦 CONSTRUCCIÓN:"
	@echo "  make build          - Construir imagen Docker"
	@echo "  make rebuild        - Reconstruir desde cero"
	@echo ""
	@echo "🚀 EJECUCIÓN:"
	@echo "  make run            - Iniciar contenedor en background con persistencia"
	@echo "  make run-it         - Iniciar contenedor interactivo"
	@echo "  make run-dev        - Iniciar en modo desarrollo (montando código local)"
	@echo ""
	@echo "🎮 CONTROL:"
	@echo "  make start          - Iniciar contenedor existente"
	@echo "  make stop           - Detener contenedor"
	@echo "  make restart        - Reiniciar contenedor"
	@echo "  make logs           - Ver logs en tiempo real"
	@echo "  make logs-tail      - Ver últimas 50 líneas"
	@echo "  make shell          - Abrir shell en el contenedor"
	@echo "  make status         - Ver estado de contenedores y volúmenes"
	@echo ""
	@echo "💾 DATOS:"
	@echo "  make volume-create  - Crear volumen para persistencia"
	@echo "  make volume-backup  - Crear backup del volumen"
	@echo "  make volume-restore - Restaurar último backup"
	@echo "  make db-shell       - Acceder a la base de datos SQLite"
	@echo ""
	@echo "🧹 LIMPIEZA:"
	@echo "  make clean          - Eliminar contenedores"
	@echo "  make clean-all      - Eliminar contenedores e imagen"
	@echo "  make clean-volume   - Eliminar volumen (⚠️  BORRA DATOS)"
	@echo "  make prune          - Limpiar recursos Docker no utilizados"
	@echo ""
	@echo "📊 UTILIDADES:"
	@echo "  make ps             - Listar contenedores"
	@echo "  make stats          - Ver estadísticas en tiempo real"
	@echo "  make inspect        - Inspeccionar contenedor"
	@echo ""
	@echo "🔧 DESARROLLO:"
	@echo "  make test           - Ejecutar tests"
	@echo "  make lint           - Ejecutar linter"
	@echo ""
	@echo "Aplicación disponible en: http://localhost:$(PORT)"

.DEFAULT_GOAL := help
