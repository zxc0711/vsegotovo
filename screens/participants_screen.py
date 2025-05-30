from kivy.uix.screenmanager import Screen

class ParticipantsScreen(Screen):
    def on_pre_enter(self):
        data = [
            "Иванов Иван",
            "Петров Петр",
            "Сидоров Сидор",
            "Николаев Николай",
            "Дмитриев Дмитрий"
        ]

        container = self.ids.participants_box
        container.clear_widgets()
        for name in data:
            from kivy.uix.label import Label
            lbl = Label(text=name, size_hint_y=None, height=40, color=(1,1,1,1))
            container.add_widget(lbl)
