import flet as ft
import random

class MetalingApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Metaling Messenger"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#000000"
        
        # Данные текущего юзера (пока пустые)
        self.user_data = {
            "email": "",
            "id": "Not Registered",
            "balance": 0,
            "is_owner": False
        }
        
        self.main_container = ft.Container(expand=True)
        self.page.add(self.main_container)
        
        # Начинаем с экрана регистрации
        self.show_registration()

    def show_registration(self):
        email_input = ft.TextField(label="Email", border_color="#007AFF", width=300)
        pass_input = ft.TextField(label="Password", password=True, can_reveal_password=True, border_color="#007AFF", width=300)
        
        def register_click(e):
            if email_input.value and pass_input.value:
                # Имитация регистрации
                self.user_data["email"] = email_input.value
                self.user_data["id"] = str(random.randint(1000000, 9999999))
                # Если это ты (админ)
                if email_input.value == "admin@metaling.com":
                    self.user_data["is_owner"] = True
                
                self.build_main_interface()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Заполни все поля!"))
                self.page.snack_bar.open = True
                self.page.update()

        self.main_container.content = ft.Column([
            ft.Image(src="https://imemessenger.com/assets/img/logo.png", width=100),
            ft.Text("Metaling Registration", size=24, weight="bold"),
            email_input,
            pass_input,
            ft.ElevatedButton("Зарегистрироваться", on_click=register_click, bgcolor="#007AFF", color="white", width=300),
            ft.Text("By creating an account, you agree to Metaling Terms", size=10, color="gray")
        ], alignment="center", horizontal_alignment="center", spacing=20)
        self.page.update()

    def build_main_interface(self):
        self.content_area = ft.Container(expand=True)
        self.nav_bar = ft.NavigationBar(
            bgcolor="#000000",
            selected_index=0,
            on_change=lambda e: self.navigate(e.control.selected_index),
            destinations=[
                ft.NavigationDestination(icon=ft.icons.CHAT_OUTLINED, label="Чаты"),
                ft.NavigationDestination(icon=ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, label="Кошелек"),
                ft.NavigationDestination(icon=ft.icons.STOREFRONT_OUTLINED, label="Магазин"),
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label="Настройки"),
            ]
        )
        
        self.main_container.content = ft.Column([
            self.content_area,
            self.nav_bar
        ], expand=True)
        self.show_chats()
        self.page.update()

    def navigate(self, index):
        if index == 0: self.show_chats()
        elif index == 1: self.show_wallet()
        elif index == 2: self.show_shop()
        elif index == 3: self.show_settings()
        self.page.update()

    def show_chats(self):
        search_field = ft.TextField(hint_text="Поиск чатов...", prefix_icon=ft.icons.SEARCH, border_radius=10, height=40)
        
        chat_list = ft.ListView(expand=True, spacing=10)
        # Пока список пуст - это реально
        chat_list.controls.append(ft.Text("У вас пока нет чатов. Воспользуйтесь поиском.", color="gray", text_align="center"))

        self.content_area.content = ft.Container(
            padding=15,
            content=ft.Column([
                ft.Text("Metaling Messenger", size=22, weight="bold"),
                search_field,
                chat_list
            ])
        )

    def show_wallet(self):
        self.content_area.content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Мои Активы", size=24, weight="bold"),
                ft.Container(
                    padding=20, border_radius=20, 
                    gradient=ft.LinearGradient(["#1e1e1e", "#0f0f0f"]),
                    content=ft.Column([
                        ft.Text("Общий баланс", color="gray"),
                        ft.Text(f"{self.user_data['balance']} LIME", size=32, weight="bold", color="white")
                    ])
                ),
                ft.Text("Транзакции", size=18, weight="bold"),
                ft.Text("История пуста", color="gray")
            ], spacing=20)
        )

    def show_shop(self):
        # Магазин теперь пуст или требует загрузки от админа
        self.content_area.content = ft.Column([
            ft.AppBar(title=ft.Text("Digital Gifts"), bgcolor="#000000"),
            ft.Container(
                expand=True, content=ft.Text("В магазине пока нет товаров. Ждите обновлений от админа.", text_align="center"),
                alignment=ft.alignment.center
            )
        ])

    def show_settings(self):
        self.content_area.content = ft.ListView([
            ft.ListTile(
                leading=ft.CircleAvatar(content=ft.Text(self.user_data["email"][0].upper())),
                title=ft.Text(self.user_data["email"]),
                subtitle=ft.Text(f"ID: {self.user_data['id']}")
            ),
            ft.Divider(),
            ft.ListTile(leading=ft.Icon(ft.icons.SECURITY), title=ft.Text("Admin Panel"), 
                        visible=self.user_data["is_owner"], on_click=lambda _: print("Admin Open"))
        ])

if __name__ == "__main__":
    ft.app(target=MetalingApp)
