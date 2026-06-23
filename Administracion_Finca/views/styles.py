# Administracion_Finca/views/styles.py
import reflex as rx

# --- Tokens de color semánticos (se adaptan a modo claro/oscuro) ---
card_bg    = rx.color_mode_cond(light="#ffffff",  dark="#1f2937")
card_border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151")
input_bg   = rx.color_mode_cond(light="#f8fafc",  dark="#374151")
text_main  = rx.color_mode_cond(light="#0f172a",  dark="#ffffff")
text_muted = rx.color_mode_cond(light="#64748b",  dark="#9ca3af")
text_sub   = rx.color_mode_cond(light="#475569",  dark="#e5e7eb")
text_accent = rx.color_mode_cond(light="#1d4ed8", dark="#60a5fa")

# --- Colores específicos de información y alertas ---
info_bg    = rx.color_mode_cond(light="#eff6ff",  dark="#1e3a8a")
info_border = rx.color_mode_cond(light="1px solid #bfdbfe", dark="1px solid #1d4ed8")
info_text  = rx.color_mode_cond(light="#1e40af",  dark="#60a5fa")
info_body  = rx.color_mode_cond(light="#374151",  dark="#d1d5db")

# Tarjetas de riesgo (roja)
risk_bg     = rx.color_mode_cond(light="#fff1f2",  dark="#7f1d1d")
risk_border = rx.color_mode_cond(light="1px solid #fca5a5", dark="1px solid #ef4444")
risk_title  = rx.color_mode_cond(light="#b91c1c",  dark="#f87171")
risk_text   = rx.color_mode_cond(light="#374151",  dark="#e5e7eb")

# Tarjetas de estrategia (verde)
strategy_bg     = rx.color_mode_cond(light="#f0fdf4",  dark="#064e3b")
strategy_border = rx.color_mode_cond(light="1px solid #86efac", dark="1px solid #10b981")
strategy_title  = rx.color_mode_cond(light="#15803d",  dark="#34d399")
strategy_text   = rx.color_mode_cond(light="#374151",  dark="#e5e7eb")

# Diagnósticos e IA
diag_box_bg     = rx.color_mode_cond(light="#f8fafc",  dark="#111827")
diag_box_border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151")
req_box_bg      = rx.color_mode_cond(light="#f5f3ff",  dark="#2e1065")
req_box_border  = rx.color_mode_cond(light="1px solid #c4b5fd", dark="1px solid #7c3aed")
req_text        = rx.color_mode_cond(light="#4c1d95",  dark="#ffffff")

# --- Tokens de Transición y Animación ---
transition_all  = "all 0.18s ease"
transition_fast = "all 0.12s ease"
transition_slow = "all 0.30s ease"
border_radius_card = "12px"
box_shadow_card = rx.color_mode_cond(
    light="0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.05)",
    dark="0 1px 3px rgba(0,0,0,0.30), 0 4px 12px rgba(0,0,0,0.25)",
)
box_shadow_card_hover = rx.color_mode_cond(
    light="0 4px 16px rgba(0,0,0,0.12), 0 1px 4px rgba(0,0,0,0.06)",
    dark="0 4px 16px rgba(0,0,0,0.40), 0 1px 4px rgba(0,0,0,0.30)",
)


# --- Componente KPI Unificado ---
def kpi_card(
    titulo: str,
    valor,
    subtitulo: str = "",
    estado: rx.Var = None,
    icono: str = None,
    color_badge: str = None,
    popover_content: rx.Component = None,
) -> rx.Component:
    """Tarjeta de KPI unificada con micro-animación hover para todo el sistema."""
    # Si se proporciona icono, usamos el modo con icono y color fijo (alimentación)
    if icono is not None:
        c_border = color_badge or "#3b82f6"
        c_bg = card_bg
        c_title = text_muted
        c_heading = text_main
        c_sub = text_sub

        icon_element = rx.icon(icono, color=c_border, size=22)
    else:
        # Modo semáforo dinámico basado en el estado (verde, amarillo, rojo)
        c_border = rx.cond(estado == "verde", "#22c55e", rx.cond(estado == "amarillo", "#fbbf24", "#ef4444"))
        c_bg = rx.cond(
            estado == "verde",
            rx.color_mode_cond(light="#dcfce7", dark="#064e3b"),
            rx.cond(
                estado == "amarillo",
                rx.color_mode_cond(light="#fef9c3", dark="#78350f"),
                rx.color_mode_cond(light="#fee2e2", dark="#7f1d1d"),
            ),
        )
        c_heading = rx.cond(
            estado == "verde",
            rx.color_mode_cond(light="#15803d", dark="#ffffff"),
            rx.cond(
                estado == "amarillo",
                rx.color_mode_cond(light="#92400e", dark="#ffffff"),
                rx.color_mode_cond(light="#991b1b", dark="#ffffff"),
            ),
        )
        c_sub = rx.cond(
            estado == "verde",
            rx.color_mode_cond(light="#166534", dark="#d1d5db"),
            rx.cond(
                estado == "amarillo",
                rx.color_mode_cond(light="#78350f", dark="#d1d5db"),
                rx.color_mode_cond(light="#7f1d1d", dark="#d1d5db"),
            ),
        )
        c_title = rx.cond(
            estado == "verde",
            rx.color_mode_cond(light="#15803d", dark="#9ca3af"),
            rx.cond(
                estado == "amarillo",
                rx.color_mode_cond(light="#92400e", dark="#9ca3af"),
                rx.color_mode_cond(light="#991b1b", dark="#9ca3af"),
            ),
        )

        icon_name = rx.cond(estado == "verde", "circle-check", rx.cond(estado == "amarillo", "triangle-alert", "circle-alert"))
        icon_color = rx.cond(estado == "verde", "#4ade80", rx.cond(estado == "amarillo", "#fbbf24", "#f87171"))
        icon_element = rx.icon(icon_name, color=icon_color, size=20)

    card_element = rx.card(
        rx.vstack(
            rx.hstack(
                icon_element,
                rx.text(titulo, font_size="0.9em", weight="bold", color=c_title),
                spacing="2",
                align="center",
            ),
            rx.heading(valor, size="6", margin_y="6px", color=c_heading, letter_spacing="-0.5px"),
            rx.text(subtitulo, font_size="0.73em", color=c_sub),
            align="start",
            spacing="1",
        ),
        border_left=f"4px solid {c_border}",
        background_color=c_bg,
        border_radius=border_radius_card,
        box_shadow=box_shadow_card,
        padding="18px",
        width="100%",
        transition=transition_all,
        _hover={"box_shadow": box_shadow_card_hover, "transform": "translateY(-2px)"},
    )

    if popover_content is not None:
        return rx.hover_card.root(
            rx.hover_card.trigger(
                rx.box(card_element, cursor="pointer")
            ),
            rx.hover_card.content(
                popover_content,
                side="bottom",
                align="center",
            ),
        )
    return card_element
