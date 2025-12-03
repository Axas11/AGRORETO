import reflex as rx

from app.components.styles import M3Styles


def index_page() -> rx.Component:
    """Página de inicio con introducción y botones para login/registro"""
    return rx.el.div(
        # Header/Navbar
        rx.el.nav(
            rx.el.div(
                rx.el.div(
                    rx.image(src="/favicon.ico", class_name="w-8 h-8"),
                    rx.el.h2(
                        "AGRORETO",
                        class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.div(
                    rx.el.a(
                        "Características",
                        href="#features",
                        class_name="text-slate-600 hover:text-blue-600 transition-colors",
                    ),
                    rx.el.a(
                        "Sobre nosotros",
                        href="#about",
                        class_name="text-slate-600 hover:text-blue-600 transition-colors",
                    ),
                    class_name="flex gap-8 items-center",
                ),
                class_name="flex justify-between items-center",
            ),
            class_name="px-8 py-4 bg-white border-b border-slate-100",
        ),
        
        # Hero Section
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        "Sistema de Monitoreo Agrícola",
                        class_name=f"text-5xl font-bold text-slate-900 mb-4 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "Monitorea sensores en tiempo real, gestiona parcelas y recibe alertas automáticas para optimizar tu producción agrícola.",
                        class_name="text-xl text-slate-600 mb-8 max-w-2xl leading-relaxed",
                    ),
                    rx.el.div(
                        rx.el.a(
                            rx.el.div(
                                rx.icon("log-in", class_name="w-5 h-5"),
                                rx.el.span("Iniciar Sesión"),
                                class_name="flex items-center gap-2",
                            ),
                            href="/login",
                            class_name=f"{M3Styles.BUTTON_PRIMARY}",
                        ),
                        rx.el.a(
                            rx.el.div(
                                rx.icon("user-plus", class_name="w-5 h-5"),
                                rx.el.span("Registrarse"),
                                class_name="flex items-center gap-2",
                            ),
                            href="/register",
                            class_name=f"border-2 border-blue-600 text-blue-600 {M3Styles.ROUNDED_FULL} px-8 py-3 font-medium hover:bg-blue-50 transition-all duration-200 flex items-center justify-center gap-2",
                        ),
                        class_name="flex gap-4 flex-wrap",
                    ),
                    class_name="flex flex-col items-start justify-center py-20",
                ),
                class_name="container mx-auto px-8",
            ),
            class_name="bg-gradient-to-br from-blue-50 to-green-50 py-20",
        ),
        
        # Features Section
        rx.el.section(
            rx.el.div(
                rx.el.h2(
                    "Características Principales",
                    id="features",
                    class_name=f"text-4xl font-bold text-slate-900 mb-12 text-center {M3Styles.FONT_FAMILY}",
                ),
                rx.el.div(
                    # Feature 1
                    rx.el.div(
                        rx.el.div(
                            rx.icon("activity", class_name="w-12 h-12 text-blue-600 mb-4"),
                            rx.el.h3(
                                "Monitoreo en Tiempo Real",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Recibe datos de múltiples sensores en tu dashboard en tiempo real.",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    # Feature 2
                    rx.el.div(
                        rx.el.div(
                            rx.icon("alert-circle", class_name="w-12 h-12 text-green-600 mb-4"),
                            rx.el.h3(
                                "Alertas Inteligentes",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Configuración automática de umbrales y notificaciones cuando se exceden.",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    # Feature 3
                    rx.el.div(
                        rx.el.div(
                            rx.icon("bar-chart-3", class_name="w-12 h-12 text-purple-600 mb-4"),
                            rx.el.h3(
                                "Análisis Histórico",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Visualiza gráficos y tendencias de tus sensores en cualquier período.",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    # Feature 4
                    rx.el.div(
                        rx.el.div(
                            rx.icon("map-pin", class_name="w-12 h-12 text-red-600 mb-4"),
                            rx.el.h3(
                                "Gestión de Parcelas",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Organiza y controla múltiples parcelas y sus sensores asociados.",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    # Feature 5
                    rx.el.div(
                        rx.el.div(
                            rx.icon("shield", class_name="w-12 h-12 text-orange-600 mb-4"),
                            rx.el.h3(
                                "Seguridad",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Acceso seguro con roles de usuario (Agricultor y Técnico).",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    # Feature 6
                    rx.el.div(
                        rx.el.div(
                            rx.icon("wifi", class_name="w-12 h-12 text-indigo-600 mb-4"),
                            rx.el.h3(
                                "API REST",
                                class_name=f"text-xl font-bold text-slate-900 mb-2 {M3Styles.FONT_FAMILY}",
                            ),
                            rx.el.p(
                                "Integración fácil con otros sistemas mediante API REST documentada.",
                                class_name="text-slate-600",
                            ),
                        ),
                        class_name=f"{M3Styles.CARD}",
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
                class_name="container mx-auto px-8 py-20",
            ),
            class_name="bg-white",
        ),
        
        # About Section
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Sobre AGRORETO",
                        id="about",
                        class_name=f"text-4xl font-bold text-slate-900 mb-6 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "AGRORETO es un sistema integral de monitoreo agrícola diseñado para maximizar la productividad de tus cultivos. "
                        "Con conexión a sensores IoT en tiempo real, podrás tomar decisiones basadas en datos precisos.",
                        class_name="text-lg text-slate-600 mb-4 leading-relaxed",
                    ),
                    rx.el.p(
                        "Nuestro sistema integra tecnologías de IoT (Internet of Things) con machine learning para proporcionar insights "
                        "accionables que te ayuden a optimizar riego, fertilizantes y labores agrícolas.",
                        class_name="text-lg text-slate-600 leading-relaxed",
                    ),
                    class_name="max-w-3xl",
                ),
                class_name="container mx-auto px-8 py-20",
            ),
            class_name="bg-slate-50",
        ),
        
        # CTA Section
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "¿Listo para comenzar?",
                        class_name=f"text-4xl font-bold text-white mb-4 text-center {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "Únete a agricultores que ya están optimizando sus cultivos con AGRORETO",
                        class_name="text-lg text-blue-100 text-center mb-8",
                    ),
                    rx.el.div(
                        rx.el.a(
                            rx.el.div(
                                rx.icon("arrow-right", class_name="w-5 h-5"),
                                rx.el.span("Registrarse Ahora"),
                                class_name="flex items-center gap-2",
                            ),
                            href="/register",
                            class_name="bg-white text-blue-600 px-8 py-3 rounded-full font-bold hover:shadow-lg transition-all duration-200 inline-flex items-center gap-2",
                        ),
                        class_name="flex justify-center",
                    ),
                    class_name="text-center",
                ),
                class_name="container mx-auto px-8 py-20",
            ),
            class_name="bg-gradient-to-r from-blue-600 to-blue-800",
        ),
        
        # Footer
        rx.el.footer(
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        "© 2025 AGRORETO. Todos los derechos reservados.",
                        class_name="text-slate-600 text-center",
                    ),
                ),
                class_name="container mx-auto px-8 py-8",
            ),
            class_name="bg-white border-t border-slate-100",
        ),
        
        class_name="min-h-screen bg-white",
    )


def index() -> rx.Component:
    return index_page()