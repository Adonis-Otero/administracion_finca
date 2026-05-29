import reflex as rx

config = rx.Config(
    app_name="Administracion_Finca",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)