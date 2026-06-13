import flet as ft
import random

class MetalingMessenger:
    def __init__(self, page: ft.Page):
        self.page = page
        self.user_id = "8091345445"
        self.is_owner = True
        self.version = "1.0.8-alpha"
        
        # Конфигурация страницы
        self.page.title = "Metaling Messenger"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#000000"
        self.page.padding = 0
        self.page.fonts = {"Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf"}
        
        self.container = ft.Container(expand=True)
        self.nav_bar = self.build_nav_bar()
        
        self.page.add(ft.Column([self.container, self.nav_bar], expand=True))
        self.show_settings()

    # --- UI HELPERS ---
    def build_nav_bar(self):
        return ft.NavigationBar(
            bgcolor="#000000", selected_index=4,
            on_change=lambda e: self.navigate(e.control.selected_index),
            destinations=[
                ft.NavigationDestination(icon=ft.icons.CHAT_OUTLINED, label="Чаты"),
                ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, label="Кошелек"),
                ft.NavigationDestination(icon=ft.icons.STOREFRONT_OUTLINED, label="Магазин"),
                ft.NavigationDestination(icon=ft.icons.AUTO_FIX_HIGH, label="M-AI"),
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label="Настройки"),
            ]
        )

    def build_tile(self, icon, color, text, trail="", action=None):
        return ft.Container(
            on_click=action,
            content=ft.ListTile(
                leading=ft.Container(ft.Icon(icon, size=20), bgcolor=color, border_radius=8, width=32, height=32),
                title=ft.Text(text, size=16),
                trailing=ft.Row([ft.Text(trail, color="#8E8E93"), ft.Icon(ft.icons.CHEVRON_RIGHT, size=18)], tight=True)
            )
        )

    # --- ЛОГИКА НАВИГАЦИИ ---
    def navigate(self, index):
        if index == 0: self.show_chats()
        elif index == 1: self.show_wallet()
        elif index == 2: self.show_shop()
        elif index == 4: self.show_settings()
        self.page.update()

    # --- ЭКРАН: МАГАЗИН (165+ NFT/GIFTS) ---
    def show_shop(self):
        items = ft.GridView(expand=True, runs_count=3, max_extent=150, child_aspect_ratio=0.8)
        # Генерируем 165+ подарков
        for i in range(1, 167):
            items.controls.append(
                ft.Container(
                    bgcolor="#1C1C1E", border_radius=12, padding=10,
                    content=ft.Column([
                        ft.Icon(ft.icons.TOKEN, color=random.choice(["#FFCC00", "#AF52DE", "#007AFF"])),
                        ft.Text(f"NFT #{i}", size=12, weight="bold"),
                        ft.Text(f"{random.randint(10, 500)} Лун", size=10, color="#8E8E93")
                    ], horizontal_alignment="center")
                )
            )
        self.container.content = ft.Column([
            ft.AppBar(title=ft.Text("Магазин Артефактов"), bgcolor="#1C1C1E"),
            items
        ], expand=True)

    # --- ЭКРАН: КОШЕЛЕК ---
    def show_wallet(self):
        self.container.content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Metaling Wallet", size=28, weight="bold"),
                ft.Container(
                    gradient=ft.LinearGradient(["#007AFF", "#5856D6"]),
                    padding=25, border_radius=20,
                    content=ft.Column([
                        ft.Text("Баланс LIME"),
                        ft.Text("12,500.00 LIME", size=32, weight="bold"),
                        ft.Text("≈ $ 1,250.00", size=14, color="white70")
                    ])
                ),
                ft.Row([
                    ft.ElevatedButton("Отправить", icon=ft.icons.SEND, expand=True),
                    ft.ElevatedButton("Получить", icon=ft.icons.QR_CODE, expand=True),
                ]),
                ft.Text("История транзакций", size=18, weight="bold"),
                ft.ListView([
                    ft.ListTile(title=ft.Text("Покупка NFT #42"), trailing=ft.Text("-50 Лун", color="red")),
                    ft.ListTile(title=ft.Text("Награда за активность"), trailing=ft.Text("+10 Лун", color="green")),
                ], expand=True)
            ], spacing=20)
        )

    # --- ЭКРАН: НАСТРОЙКИ + АДМИНКА ---
    def show_settings(self):
        self.container.content = ft.ListView([
            ft.Container(height=40),
            ft.ListTile(
                leading=ft.CircleAvatar(content=ft.Text("P"), radius=30, bgcolor="#007AFF"),
                title=ft.Text("Profik", size=22, weight="bold"),
                subtitle=ft.Text(f"ID: {self.user_id} | Владелец OS"),
            ),
            ft.Container(height=10),
            ft.Container(bgcolor="#1C1C1E", border_radius=15, margin=15, content=ft.Column([
                self.build_tile(ft.icons.STAR, "#FFCC00", "Металинг Луны", "1,250 🌙"),
                self.build_tile(ft.icons.AUTO_AWESOME, "#AF52DE", "Metaling Premium"),
                self.build_tile(ft.icons.BUSINESS_CENTER, "#007AFF", "Metaling Business"),
            ], spacing=0)),
            ft.Container(bgcolor="#1C1C1E", border_radius=15, margin=15, content=ft.Column([
                self.build_tile(ft.icons.ACCOUNT_BALANCE_WALLET, "#34C759", "Кошелек"),
                self.build_tile(ft.icons.COLOR_LENS, "#FF3B30", "Оформление"),
                self.build_tile(ft.icons.BUILD, "#8E8E93", "Инструменты"),
            ], spacing=0)),
            ft.Container(
                margin=15,
                content=ft.ElevatedButton(
                    "ПАНЕЛЬ ВЛАДЕЛЬЦА (40+ ФУНКЦИЙ)", 
                    icon=ft.icons.SECURITY, bgcolor="red", color="white", height=55,
                    on_click=self.open_admin, visible=self.is_owner
                )
            ),
            ft.Text(f"Metaling Messenger v{self.version}", size=12, color="#444444", text_align="center")
        ])

    def open_admin(self, e):
        self.page.bottom_sheet = ft.BottomSheet(
            ft.Container(
                padding=20, bgcolor="#121212",
                content=ft.Column([
                    ft.Text("🛡 УПРАВЛЕНИЕ METALING OS", size=20, weight="bold", color="red"),
                    ft.Divider(color="red"),
                    ft.Tabs(
                        tabs=[
                            ft.Tab(text="Юзеры", content=ft.ListView([ft.Switch(label=f"Бан по ID {i+100}") for i in range(15)], height=400)),
                            ft.Tab(text="Экономика", content=ft.ListView([ft.Switch(label=f"Бонус Лун {i*10}%") for i in range(10)], height=400)),
                            ft.Tab(text="NFT", content=ft.Column([
                                ft.ElevatedButton("Создать новый NFT-подарок", icon=ft.icons.ADD_A_PHOTO),
                                ft.TextField(label="ID Подарка"),
                                ft.Switch(label="Активен в магазине", value=True)
                            ])),
                        ]
                    )
                ], tight=True)
            ), is_scroll_controlled=True
        )
        self.page.bottom_sheet.open = True
        self.page.update()

    def show_chats(self):
        self.container.content = ft.Column([
            ft.AppBar(title=ft.Text("Metaling Messenger"), bgcolor="#1C1C1E"),
            ft.ListView([
                ft.ListTile(leading=ft.CircleAvatar(bgcolor=random.choice(["red", "blue", "green"])), title=ft.Text(f"Пользователь {i}"), subtitle=ft.Text("Привет! Как работает Metaling?"))
                for i in range(12)
            ], expand=True)
        ])

if __name__ == "__main__":
    ft.app(target=MetalingMessenger)
