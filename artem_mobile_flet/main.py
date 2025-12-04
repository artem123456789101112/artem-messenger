# ARTEM Messenger - Kivy версия
import kivy
kivy.require('2.3.0')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class ARTEMApp(App):
    def build(self):
        self.title = 'ARTEM Messenger'
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(
            text='ARTEM Messenger',
            font_size=30,
            bold=True
        ))
        
        layout.add_widget(Label(
            text='Build with GitHub Actions',
            font_size=20
        ))
        
        layout.add_widget(Label(
            text='Status: SUCCESS!',
            font_size=20,
            color=(0, 1, 0, 1)  # Зеленый
        ))
        
        btn = Button(
            text='Click Me!',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5}
        )
        btn.bind(on_press=self.on_button_click)
        layout.add_widget(btn)
        
        return layout
    
    def on_button_click(self, instance):
        print("Button clicked!")
        # Можно добавить логику

if __name__ == '__main__':
    ARTEMApp().run()
