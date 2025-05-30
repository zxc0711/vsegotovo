class AddOrderFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#F0F0F0")  # Светлый фон

        self.label = ctk.CTkLabel(self, text="Добавление заказа", font=("Arial", 20, "bold"), text_color="#333333")
        self.label.pack(pady=10)

        # Поле для выбора товара
        self.product_label = ctk.CTkLabel(self, text="Товар:", text_color="#333333", font=("Arial", 14))
        self.product_label.pack(pady=5)

        # Поле поиска товаров
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_products)
        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            fg_color="#FFFFFF",
            text_color="#333333",
            font=("Arial", 14),
            placeholder_text="Поиск товара..."
        )
        self.search_entry.pack(pady=5)

        self.product_combobox = ctk.CTkComboBox(
            self,
            values=[p["name"] for p in products],
            fg_color="#FFFFFF",
            button_color="#4CAF50",
            text_color="#333333",
            font=("Arial", 14)
        )
        self.product_combobox.pack(pady=5)

        self.quantity_label = ctk.CTkLabel(self, text="Количество:", text_color="#333333", font=("Arial", 14))
        self.quantity_label.pack(pady=5)
        self.quantity_entry = ctk.CTkEntry(
            self,
            fg_color="#FFFFFF",
            text_color="#333333",
            font=("Arial", 14),
            placeholder_text="Введите количество"
        )
        self.quantity_entry.pack(pady=5)

        self.save_button = ctk.CTkButton(
            self,
            text="Сохранить заказ",
            command=self.save_order,
            fg_color="#4CAF50",
            hover_color="#45A049",
            text_color="#FFFFFF",
            font=("Arial", 14, "bold"),
            corner_radius=10
        )
        self.save_button.pack(pady=10)
    def filter_products(self, *args):
        """Фильтрация товаров по мере ввода"""
        search_text = self.search_var.get().lower()
        filtered_products = [p["name"] for p in products if search_text in p["name"].lower()]
        self.product_combobox.configure(values=filtered_products)
    def save_order(self):
        product_name = self.product_combobox.get()
        quantity = self.quantity_entry.get()

        if not product_name or not quantity.isdigit():
            messagebox.showerror("Ошибка", "Проверьте введенные данные.")
            return

        product = next((p for p in products if p["name"] == product_name), None)
        if product:
            # Проверяем, существует ли уже такой заказ
            existing_order = next((o for o in orders if o["product_id"] == product["id"]), None)
            if existing_order:
                existing_order["quantity"] += int(quantity)
                messagebox.showinfo("Успешно", f"Количество товара '{product_name}' увеличено на {quantity}.")
            else:
                order = {"product_id": product["id"], "product_name": product["name"], "quantity": int(quantity)}
                orders.append(order)
                messagebox.showinfo("Успешно", f"Заказ сохранен: {product['name']}, количество: {quantity}")
            self.search_var.set("")  # Очищаем поля
            self.quantity_entry.delete(0, "end")
        else:
            messagebox.showerror("Ошибка", "Товар не найден.")