import os
import discord
from discord.ext import commands
from discord import app_commands

# ============================================================
# CONFIGURACIÓN
# ============================================================
# Puedes dejar estos valores vacíos y configurarlos con /config
# directamente desde Discord.
TOKEN = "MTUzNTczMzA1OTg2NzkwMTk3Mg.GQqbs5.CjY8ueR75aQgB3GWhvuqXWqHN6C9IgqBETViHU"

# IDs de canales de texto
REQUEST_PANEL_CHANNEL_ID = 1535744261037887570
REQUESTS_CHANNEL_ID = 1535747659065729074

# ID del rol que puede aceptar/rechazar solicitudes
APPROVER_ROLE_ID = 1292240348898267377

# IDs de las 5 salas de voz
VOICE_CHANNEL_IDS = [1292224467325419530, 1292221416711651432, 1292224551060766842, 1326145124866064456, 1326145263064059966]

VOICE_NAMES = [
    "👧●𝙎𝙪𝙥𝙚𝙧𝙣𝙚𝙣𝙖𝙨  1●👧",
    "👧●𝙎𝙪𝙥𝙚𝙧𝙣𝙚𝙣𝙖𝙨  2●👧",
    "👧●𝙎𝙪𝙥𝙚𝙧𝙣𝙚𝙣𝙖𝙨  3●👧",
    "👧●𝙎𝙪𝙥𝙚𝙧𝚗𝚎𝚗𝚊𝚜  4●👧",
    "👧●𝙎𝙪𝙥𝚎𝚛𝚗𝚎𝚗𝚊𝚜  5●👧",
]

# ============================================================
# BOT
# ============================================================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# user_id -> {"target": voice_channel_id, "message_id": int}
pending = {}


def configured():
    return (
        REQUEST_PANEL_CHANNEL_ID != 0
        and REQUESTS_CHANNEL_ID != 0
        and APPROVER_ROLE_ID != 0
        and len(VOICE_CHANNEL_IDS) == 5
        and all(VOICE_CHANNEL_IDS)
    )


def voice_status(guild):
    rows = []
    for i, channel_id in enumerate(VOICE_CHANNEL_IDS):
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            rows.append(f"{VOICE_NAMES[i]} — **canal no configurado**")
            continue

        members = channel.members
        if members:
            names = ", ".join(m.display_name for m in members)
            rows.append(
                f"{channel.mention} — **{len(members)} persona(s)**\n"
                f"👤 {names}"
            )
        else:
            rows.append(f"{channel.mention} — **0 personas**")
    return "\n\n".join(rows)


def panel_embed(guild):
    return discord.Embed(
        title="🎤 Solicita entrar a una sala",
        description=(
            "Pulsa **solicitar-unirse** para consultar las salas disponibles "
            "y solicitar acceso a una de ellas.\n\n"
            "### Salas actuales\n"
            f"{voice_status(guild)}"
        ),
        color=discord.Color.blurple(),
    )


class RequestButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="solicitar-unirse",
            style=discord.ButtonStyle.primary,
            custom_id="voice_request:start",
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message(
                "Este botón solo funciona dentro del servidor.",
                ephemeral=True,
            )

        if not configured():
            return await interaction.response.send_message(
                "El bot todavía no está configurado. Usa `/config`.",
                ephemeral=True,
            )

        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            return await interaction.response.send_message(
                "🎤 Primero debes estar conectado a un canal de voz.",
                ephemeral=True,
            )

        if interaction.user.id in pending:
            return await interaction.response.send_message(
                "⏳ Ya tienes una solicitud pendiente.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            "Selecciona la sala a la que quieres solicitar unirte:",
            view=VoiceSelectView(),
            ephemeral=True,
        )


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RequestButton())


class VoiceSelectButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(
            label=f"Supernenas {index + 1}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"voice_request:select:{index}",
        )
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            return await interaction.response.send_message(
                "🎤 Primero debes estar conectado a un canal de voz.",
                ephemeral=True,
            )

        target_id = VOICE_CHANNEL_IDS[self.index]
        target = interaction.guild.get_channel(target_id)
        if not isinstance(target, discord.VoiceChannel):
            return await interaction.response.send_message(
                "❌ Esa sala no está configurada correctamente.",
                ephemeral=True,
            )

        requests_channel = interaction.guild.get_channel(REQUESTS_CHANNEL_ID)
        if not isinstance(requests_channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ El canal de solicitudes no está configurado.",
                ephemeral=True,
            )

        # Evita que una persona tenga varias solicitudes.
        if interaction.user.id in pending:
            return await interaction.response.send_message(
                "⏳ Ya tienes una solicitud pendiente.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title="🔔 Nueva solicitud",
            description=(
                f"👤 {member.mention} solicita entrar.\n"
                f"🎤 Canal actual: {member.voice.channel.mention}\n"
                f"🎯 Canal solicitado: {target.mention}"
            ),
            color=discord.Color.orange(),
        )
        embed.set_footer(
            text="Solo el rol autorizado puede aceptar o rechazar esta solicitud."
        )

        message = await requests_channel.send(
            embed=embed,
            view=ApprovalView(
                requester_id=member.id,
                target_channel_id=target.id,
            ),
        )

        pending[member.id] = {
            "target": target.id,
            "message_id": message.id,
        }

        await interaction.response.edit_message(
            content=f"✅ Solicitud enviada para {target.mention}.",
            embed=None,
            view=None,
        )


class VoiceSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        for i in range(5):
            self.add_item(VoiceSelectButton(i))


class ApprovalView(discord.ui.View):
    def __init__(self, requester_id, target_channel_id):
        super().__init__(timeout=3600)
        self.requester_id = requester_id
        self.target_channel_id = target_channel_id

        accept = discord.ui.Button(
            label="Aceptar",
            style=discord.ButtonStyle.success,
            custom_id=f"voice_request:accept:{requester_id}",
        )
        reject = discord.ui.Button(
            label="Rechazar",
            style=discord.ButtonStyle.danger,
            custom_id=f"voice_request:reject:{requester_id}",
        )

        async def accept_callback(interaction):
            await self.handle_approval(interaction, True)

        async def reject_callback(interaction):
            await self.handle_approval(interaction, False)

        accept.callback = accept_callback
        reject.callback = reject_callback
        self.add_item(accept)
        self.add_item(reject)

    async def handle_approval(self, interaction, accepted):
        if not interaction.guild:
            return

        role = interaction.guild.get_role(APPROVER_ROLE_ID)
        if role is None or role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ No tienes permiso para gestionar solicitudes.",
                ephemeral=True,
            )

        requester = interaction.guild.get_member(self.requester_id)
        target = interaction.guild.get_channel(self.target_channel_id)

        if not isinstance(target, discord.VoiceChannel):
            return await interaction.response.send_message(
                "❌ El canal de destino ya no existe o no está configurado.",
                ephemeral=True,
            )

        if not accepted:
            pending.pop(self.requester_id, None)
            await interaction.response.defer()
            try:
                await interaction.message.delete()
            except discord.HTTPException:
                pass
            return

        if requester is None:
            pending.pop(self.requester_id, None)
            return await interaction.response.edit_message(
                content="❌ El usuario ya no está en el servidor.",
                embed=None,
                view=None,
            )

        if not requester.voice or not requester.voice.channel:
            pending.pop(self.requester_id, None)
            return await interaction.response.edit_message(
                content="❌ El usuario ya no está conectado a un canal de voz.",
                embed=None,
                view=None,
            )

        try:
            await requester.move_to(
                target,
                reason=f"Solicitud de voz aceptada por {interaction.user}",
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ No puedo mover al usuario. Comprueba que tengo el permiso "
                "**Mover miembros** y que mi rol está por encima del usuario.",
                ephemeral=True,
            )
        except discord.HTTPException as exc:
            return await interaction.response.send_message(
                f"❌ Discord rechazó el movimiento: `{exc}`",
                ephemeral=True,
            )

        pending.pop(self.requester_id, None)
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass


@bot.event
async def on_ready():
    bot.add_view(PanelView())

    guild = discord.Object(id=1292221416128647291)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    print(f"Conectado como {bot.user} (ID: {bot.user.id})")


@bot.tree.command(name="panel", description="Publica el panel para solicitar una sala de voz.")
async def panel(interaction: discord.Interaction):
    if not configured():
        return await interaction.response.send_message(
            "❌ Configura primero el bot con `/config`.",
            ephemeral=True,
        )

    await interaction.channel.send(
        embed=panel_embed(interaction.guild),
        view=PanelView(),
    )
    await interaction.response.send_message(
        "✅ Panel publicado.",
        ephemeral=True,
    )


@bot.tree.command(name="salas", description="Muestra el estado actual de las cinco salas.")
async def salas(interaction: discord.Interaction):
    if not interaction.guild:
        return
    embed = panel_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="config", description="Muestra qué datos debes configurar en el archivo config.")
@app_commands.checks.has_permissions(administrator=True)
async def config(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Edita `bot.py` al principio del archivo y coloca los IDs de:\n"
        "• REQUEST_PANEL_CHANNEL_ID\n"
        "• REQUESTS_CHANNEL_ID\n"
        "• APPROVER_ROLE_ID\n"
        "• VOICE_CHANNEL_IDS (los 5 canales)\n\n"
        "Después reinicia el bot. El token debe ir en la variable de entorno "
        "`DISCORD_TOKEN`.",
        ephemeral=True,
    )


@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ No tienes permisos para usar este comando.",
                ephemeral=True,
            )
        return
    raise error


if not TOKEN:
    print("Falta DISCORD_TOKEN. Configúralo como variable de entorno.")
else:
    bot.run(TOKEN)
