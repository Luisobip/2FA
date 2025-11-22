# Nombre de la imagen Docker
IMAGE := 2FA

# Carpeta del proyecto dentro del contenedor
WORKDIR := /opt/project

# Ruta local del proyecto
LOCALDIR := $(shell pwd)

# ----------------------------------------------------------------
# Construcción de la imagen
# ----------------------------------------------------------------
build:
	docker build -t $(IMAGE) .


# ----------------------------------------------------------------
# Shell interactivo
# ----------------------------------------------------------------
shell:
	docker run -it \
		--shm-size=24g \
		-e DISPLAY=:0 \
		-e QT_X11_NO_MITSHM=1 \
		-v $(LOCALDIR):$(WORKDIR) \
		-v /tmp/.X11-unix:/tmp/.X11-unix \
		--rm \
		$(IMAGE) /bin/bash

# ----------------------------------------------------------------
# Recetas para ejecutar el main
# ----------------------------------------------------------------
run-blip:
	docker run -it \
		--shm-size=24g \
		-v $(LOCALDIR):$(WORKDIR) \
		--rm \
		$(IMAGE) python $(WORKDIR)/main.py

# ----------------------------------------------------------------
# Ayuda
# ----------------------------------------------------------------
help:
	@echo "make build        → Construir la imagen Docker"
	@echo "make shell        → Abrir un shell interactivo en el contenedor"
	@echo "make run-main     → Ejecutar main.py"
