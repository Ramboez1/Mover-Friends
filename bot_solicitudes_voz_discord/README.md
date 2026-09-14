# Bot de solicitudes de voz

Bot de Discord personalizado para:
- botón `solicitar-unirse`;
- mostrar las 5 salas de voz y sus ocupantes;
- crear solicitudes en un canal de texto;
- botones Aceptar/Rechazar;
- restringir la gestión al rol configurado;
- mover automáticamente al solicitante al aceptar.

## 1. Crear el bot

1. Entra en https://discord.com/developers/applications
2. `New Application` y ponle un nombre.
3. En `Bot`, pulsa `Add Bot`.
4. Copia el token y NO lo compartas.
5. En `Installation`/`OAuth2`, instala la aplicación en tu servidor.
6. Concede los permisos `View Channels`, `Send Messages`, `Embed Links`, `Read Message History` y `Move Members`.
7. En `Bot > Privileged Gateway Intents`, activa `Server Members Intent` y `Presence Intent` si aparecen; el código usa especialmente miembros y estados de voz.

## 2. Obtener IDs de Discord

Activa Discord Developer Mode:
`Ajustes de usuario > Avanzado > Modo desarrollador`.

Después:
- clic derecho al canal de texto del panel -> `Copiar ID`;
- clic derecho al canal de solicitudes -> `Copiar ID`;
- clic derecho al rol `⚫❌📄Negro Sin Papeles📄❌⚫` -> `Copiar ID`;
- clic derecho en cada una de las 5 salas de voz -> `Copiar ID`.

Pega los números en la sección CONFIGURACIÓN de `bot.py`.

## 3. Instalar y ejecutar

Necesitas Python 3.11 o superior.

En la carpeta del bot:

Windows:
```powershell
py -m pip install -r requirements.txt
$env:DISCORD_TOKEN="TU_TOKEN"
py bot.py
```

macOS/Linux:
```bash
python3 -m pip install -r requirements.txt
export DISCORD_TOKEN="TU_TOKEN"
python3 bot.py
```

El bot debe quedar ejecutándose para funcionar.

## 4. Publicar el panel

Cuando el bot esté online, ve al canal configurado y ejecuta:

`/panel`

Necesitas permiso `Administrar servidor` para usar el comando.

## 5. Permisos importantes

El rol del bot debe estar suficientemente alto en la jerarquía para poder mover a los miembros.

Si aparece `No puedo mover al usuario`, comprueba:
- el bot tiene `Mover miembros`;
- el bot puede ver los canales;
- el rol del bot está por encima del usuario que intenta mover;
- el canal de destino permite al bot acceder.

## 6. Comandos

`/panel` - publica el panel.
`/salas` - muestra las 5 salas y quién está en cada una.
`/config` - recuerda qué IDs hay que configurar (solo administrador).

## Importante sobre el token

No pongas el token dentro de un mensaje de Discord ni lo subas a GitHub.
Si alguna vez lo expones, regénéralo desde el Developer Portal.
