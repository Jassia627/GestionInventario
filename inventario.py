import os
import sys
import pandas as pd
from datetime import datetime
from math import ceil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QDialog, QFileDialog,
    QSpinBox, QMessageBox, QInputDialog, QFormLayout, QDialogButtonBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Define paths
current_dir = os.path.dirname(os.path.abspath(__file__))
inventory_path = resource_path(os.path.join('data', 'inventario.csv'))
sales_path = resource_path(os.path.join('data', 'sales.csv'))
config_path = resource_path(os.path.join('data', 'config.csv'))

# Ensure the data directory exists
os.makedirs(os.path.join(current_dir, 'data'), exist_ok=True)

def round_up_to_nearest_ten(n):
    """Redondea al alza a la decena más cercana."""
    return ceil(n / 10.0) * 10

def load_config():
    """Carga la configuración desde un archivo CSV."""
    if os.path.exists(config_path):
        return pd.read_csv(config_path)
    else:
        # Configuración predeterminada
        default_config = pd.DataFrame({'parametro': ['porcentaje_incremento'], 'valor': [30]})
        save_config(default_config)
        return default_config

def save_config(df):
    """Guarda la configuración en un archivo CSV."""
    df.to_csv(config_path, index=False)

def get_config_value(param):
    """Obtiene el valor de un parámetro de configuración."""
    config_df = load_config()
    return config_df.loc[config_df['parametro'] == param, 'valor'].values[0]

def load_inventory():
    """Carga el inventario desde un archivo CSV, ajustando precios."""
    try:
        df = pd.read_csv(inventory_path)
        if 'porcentaje_incremento' not in df.columns:
            df['porcentaje_incremento'] = get_config_value('porcentaje_incremento')
        df['precio_venta'] = df['precio'] * (1 + df['porcentaje_incremento'] / 100)
        df['precio_venta'] = df['precio_venta'].apply(round_up_to_nearest_ten)  # Redondear a la decena más cercana superior
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['id_producto', 'nombre', 'precio', 'stock', 'porcentaje_incremento', 'precio_venta'])

def save_inventory(df):
    """Guarda el inventario en un archivo CSV."""
    df.to_csv(inventory_path, index=False)

def load_sales():
    """Carga el registro de ventas desde un archivo CSV."""
    if not os.path.exists(sales_path):
        df = pd.DataFrame(columns=['fecha', 'id_producto', 'nombre', 'cantidad', 'total'])
        df.to_csv(sales_path, index=False)
    return pd.read_csv(sales_path)

def save_sales(df):
    """Guarda el registro de ventas en un archivo CSV."""
    df.to_csv(sales_path, index=False)

class InventoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Inventario")
        self.setGeometry(100, 100, 1000, 700)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.sales_tab = QWidget()
        self.inventory_tab = QWidget()
        self.sales_record_tab = QWidget()
        self.settings_tab = QWidget()
        
        self.tabs.addTab(self.sales_tab, "Ventas")
        self.tabs.addTab(self.inventory_tab, "Inventario")
        self.tabs.addTab(self.sales_record_tab, "Registro de Ventas del Día")
        self.tabs.addTab(self.settings_tab, "Configuración")
        
        self.create_sales_tab()
        self.create_inventory_tab()
        self.create_sales_record_tab()
        self.create_settings_tab()
        
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
    QMainWindow {
        background-color: #f0f0f0;
    }
    QTabWidget::pane {
        border: 1px solid #cccccc;
        background: white;
    }
    QTabBar::tab {
        background: #dcdcdc;
        border: 1px solid #cccccc;
        padding: 10px 20px; /* Aumenta el espaciado interno de cada pestaña */
        min-width: 200px; /* Establece un ancho mínimo para las pestañas */
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background: white;
        border-bottom-color: white;
    }
    QTableWidget {
        border: 1px solid #cccccc;
        background: #fafafa;
        alternate-background-color: #e8f4fc;
        selection-background-color: #a8d8ff;
        selection-color: #000000;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        padding: 15px 30px; /* Aumenta el espaciado interno del botón */
        border: none;
        border-radius: 5px;
        font-size: 18px; /* Aumenta el tamaño de fuente */
        min-width: 250px; /* Establece un ancho mínimo para los botones */
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QLabel, QLineEdit {
        font-size: 14px;
    }
    QLineEdit {
        padding: 5px;
        border: 1px solid #cccccc;
        border-radius: 3px;
    }
    QHeaderView::section {
        background-color: #dcdcdc;
        padding: 5px;
        border: 1px solid #cccccc;
    }
""")
        
    def create_sales_tab(self):
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar por nombre:")
        self.sales_search_entry = QLineEdit()
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.update_sales_tree)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.sales_search_entry)
        search_layout.addWidget(search_button)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels(['ID Producto', 'Nombre', 'Precio Venta', 'Stock'])
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setSelectionMode(QTableWidget.SingleSelection)
        self.sales_table.doubleClicked.connect(self.on_sales_item_select)
        
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setAlternatingRowColors(True)
        
        self.selected_products = {}
        self.selected_frame = QVBoxLayout()
        self.selected_frame.addWidget(QLabel("Productos Seleccionados"))
        
        sell_button = QPushButton("Vender")
        sell_button.clicked.connect(self.sell_products)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.sales_table)
        layout.addLayout(self.selected_frame)
        layout.addWidget(sell_button)
        
        self.sales_tab.setLayout(layout)
        self.update_sales_tree()
        
    def create_inventory_tab(self):
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar por nombre:")
        self.inventory_search_entry = QLineEdit()
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.update_inventory_tree)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.inventory_search_entry)
        search_layout.addWidget(search_button)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels(['ID Producto', 'Nombre', 'Precio Mayorista', 'Stock', 'Precio Venta'])
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inventory_table.setSelectionMode(QTableWidget.SingleSelection)
        
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setAlternatingRowColors(True)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("Agregar Producto")
        add_button.clicked.connect(self.add_product)
        edit_button = QPushButton("Editar Producto")
        edit_button.clicked.connect(self.edit_product)
        update_button = QPushButton("Actualizar Inventario")
        update_button.clicked.connect(self.update_inventory_tree)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(update_button)
        
        layout.addLayout(search_layout)
        layout.addWidget(self.inventory_table)
        layout.addLayout(button_layout)
        
        self.inventory_tab.setLayout(layout)
        self.update_inventory_tree()
        
    def create_sales_record_tab(self):
        layout = QVBoxLayout()
        show_button = QPushButton("Mostrar Ventas del Día")
        show_button.clicked.connect(self.record_sales_day)
        layout.addWidget(show_button)
        self.sales_record_tab.setLayout(layout)
        
    def create_settings_tab(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        self.increment_entry = QLineEdit()
        self.increment_entry.setText(str(get_config_value('porcentaje_incremento')))
        form_layout.addRow("Porcentaje de Incremento:", self.increment_entry)
        
        save_button = QPushButton("Guardar")
        save_button.clicked.connect(self.save_settings)
        
        backup_inventory_button = QPushButton("Copia de Seguridad del Inventario")
        backup_inventory_button.clicked.connect(lambda: self.backup_file(inventory_path))
        backup_sales_button = QPushButton("Copia de Seguridad de Ventas")
        backup_sales_button.clicked.connect(lambda: self.backup_file(sales_path))
        
        layout.addLayout(form_layout)
        layout.addWidget(save_button)
        layout.addWidget(backup_inventory_button)
        layout.addWidget(backup_sales_button)
        
        self.settings_tab.setLayout(layout)
        
    def update_inventory_tree(self):
        query = self.inventory_search_entry.text()
        inventory_df = load_inventory()
        if query:
            filtered_df = inventory_df[inventory_df['nombre'].str.contains(query, case=False, na=False)]
        else:
            filtered_df = inventory_df
            
        self.inventory_table.setRowCount(len(filtered_df))
        for i, row in filtered_df.iterrows():
            self.inventory_table.setItem(i, 0, QTableWidgetItem(str(row['id_producto'])))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(row['nombre']))
            self.inventory_table.setItem(i, 2, QTableWidgetItem(str(row['precio'])))
            self.inventory_table.setItem(i, 3, QTableWidgetItem(str(row['stock'])))
            self.inventory_table.setItem(i, 4, QTableWidgetItem(str(row['precio_venta'])))
            
    def update_sales_tree(self):
        query = self.sales_search_entry.text()
        inventory_df = load_inventory()
        if query:
            filtered_df = inventory_df[inventory_df['nombre'].str.contains(query, case=False, na=False)]
        else:
            filtered_df = inventory_df
            
        self.sales_table.setRowCount(len(filtered_df))
        for i, row in filtered_df.iterrows():
            self.sales_table.setItem(i, 0, QTableWidgetItem(str(row['id_producto'])))
            self.sales_table.setItem(i, 1, QTableWidgetItem(row['nombre']))
            self.sales_table.setItem(i, 2, QTableWidgetItem(str(row['precio_venta'])))
            self.sales_table.setItem(i, 3, QTableWidgetItem(str(row['stock'])))
            
    def on_sales_item_select(self):
        selected_row = self.sales_table.currentRow()
        item_id = self.sales_table.item(selected_row, 0).text()
        nombre = self.sales_table.item(selected_row, 1).text()
        stock = int(self.sales_table.item(selected_row, 3).text())
        cantidad, ok = QInputDialog.getInt(self, "Cantidad", f"Ingrese la cantidad a vender de {nombre}:", min=1, max=stock)
        
        if ok:
            self.add_to_selected(item_id, cantidad, nombre)
            
    def add_to_selected(self, item_id, cantidad, nombre):
        if item_id not in self.selected_products:
            self.selected_products[item_id] = cantidad
            label = QLabel(f"{nombre}: {cantidad} unidades")
            self.selected_frame.addWidget(label)
            
    def sell_products(self):
        total_venta = 0
        inventory_df = load_inventory()
        sales_df = load_sales()
        factura_items = []
        
        for item_id, cantidad in self.selected_products.items():
            item_row = inventory_df[inventory_df['id_producto'] == int(item_id)].iloc[0]
            nombre = item_row['nombre']
            precio_venta = item_row['precio_venta']
            total_item = float(precio_venta) * cantidad
            total_venta += total_item
            
            factura_items.append(f"{nombre}: {cantidad} unidades x ${float(precio_venta):.2f} = ${total_item:.2f}")
            
            inventory_df.loc[inventory_df['id_producto'] == int(item_id), 'stock'] -= cantidad
            
            new_sale = pd.DataFrame([{
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'id_producto': item_id,
                'nombre': nombre,
                'cantidad': cantidad,
                'total': total_item
            }])
            sales_df = pd.concat([sales_df, new_sale], ignore_index=True)
            
        save_inventory(inventory_df)
        save_sales(sales_df)
        
        factura_detalles = "\n".join(factura_items)
        QMessageBox.information(self, "Factura", f"Detalles de la venta:\n{factura_detalles}\n\nTotal a Pagar: ${total_venta:.2f}")
        
        self.update_sales_tree()
        for i in reversed(range(self.selected_frame.count())):
            widget = self.selected_frame.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.selected_products.clear()
        
    def add_product(self):
        dialog = ProductDialog(self, "Agregar Producto")
        dialog.exec_()
        if dialog.result() == QDialog.Accepted:
            product_id, name, price, stock, increment = dialog.get_values()
            inventory_df = load_inventory()
            precio_venta = round_up_to_nearest_ten(price * (1 + increment / 100))
            inventory_df.loc[len(inventory_df)] = [product_id, name, price, stock, increment, precio_venta]
            save_inventory(inventory_df)
            self.update_inventory_tree()
        
    def edit_product(self):
        selected_row = self.inventory_table.currentRow()
        if selected_row == -1:
            QMessageBox.critical(self, "Error", "No hay productos seleccionados para editar.")
            return
        
        item_id = int(self.inventory_table.item(selected_row, 0).text())
        inventory_df = load_inventory()
        product_details = inventory_df[inventory_df['id_producto'] == item_id].iloc[0]
        
        dialog = ProductDialog(self, "Editar Producto", product_details)
        dialog.exec_()
        if dialog.result() == QDialog.Accepted:
            product_id, name, price, stock, increment = dialog.get_values()
            idx = inventory_df.index[inventory_df['id_producto'] == product_id].tolist()[0]
            precio_venta = round_up_to_nearest_ten(price * (1 + increment / 100))
            inventory_df.at[idx, 'nombre'] = name
            inventory_df.at[idx, 'precio'] = price
            inventory_df.at[idx, 'stock'] = stock
            inventory_df.at[idx, 'porcentaje_incremento'] = increment
            inventory_df.at[idx, 'precio_venta'] = precio_venta
            save_inventory(inventory_df)
            self.update_inventory_tree()
        
    def record_sales_day(self):
        sales_df = load_sales()
        today = datetime.now().strftime('%Y-%m-%d')
        today_sales = sales_df[sales_df['fecha'] == today]
        
        if today_sales.empty:
            QMessageBox.information(self, "Registro de Ventas", "No se encontraron registros de ventas para hoy.")
        else:
            ventas_detalles = []
            total_ventas = today_sales['total'].sum()
            for _, row in today_sales.iterrows():
                ventas_detalles.append(f"{row['nombre']}: {row['cantidad']} unidades x ${float(row['total']) / row['cantidad']:.2f} = ${float(row['total']):.2f}")
                
            ventas_detalles_str = "\n".join(ventas_detalles)
            QMessageBox.information(self, "Registro de Ventas", f"Ventas del día:\n{ventas_detalles_str}\n\nTotal de ventas de hoy: ${total_ventas:.2f}")
            
    def save_settings(self):
        try:
            new_increment = float(self.increment_entry.text())
            config_df = load_config()
            config_df.loc[config_df['parametro'] == 'porcentaje_incremento', 'valor'] = new_increment
            save_config(config_df)
            QMessageBox.information(self, "Configuración", "Configuración guardada correctamente.")
        except ValueError:
            QMessageBox.critical(self, "Error", "Porcentaje de incremento inválido. Por favor, ingrese un número válido.")
        
    def backup_file(self, file_path):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        backup_path, _ = QFileDialog.getSaveFileName(self, "Guardar Copia de Seguridad", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if backup_path:
            try:
                with open(file_path, 'r') as f:
                    data = f.read()
                with open(backup_path, 'w') as f:
                    f.write(data)
                QMessageBox.information(self, "Copia de Seguridad", f"Copia de seguridad realizada con éxito en: {backup_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo realizar la copia de seguridad: {str(e)}")

class ProductDialog(QDialog):
    def __init__(self, parent=None, title="Agregar Producto", product_details=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setGeometry(100, 100, 300, 250)
        
        self.form_layout = QFormLayout()
        
        self.id_entry = QLineEdit()
        self.name_entry = QLineEdit()
        self.price_entry = QLineEdit()
        self.stock_entry = QLineEdit()
        self.increment_entry = QLineEdit()
        
        self.form_layout.addRow("ID Producto:", self.id_entry)
        self.form_layout.addRow("Nombre:", self.name_entry)
        self.form_layout.addRow("Precio (Mayorista):", self.price_entry)
        self.form_layout.addRow("Stock:", self.stock_entry)
        self.form_layout.addRow("Porcentaje de Incremento:", self.increment_entry)
        
        if product_details is not None:
            self.id_entry.setText(str(product_details['id_producto']))
            self.id_entry.setDisabled(True)
            self.name_entry.setText(product_details['nombre'])
            self.price_entry.setText(str(product_details['precio']))
            self.stock_entry.setText(str(product_details['stock']))
            self.increment_entry.setText(str(product_details['porcentaje_incremento']))
            
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.button_box)
        
        self.setLayout(self.layout)
        
    def get_values(self):
        return (int(self.id_entry.text()), self.name_entry.text(), float(self.price_entry.text()), int(self.stock_entry.text()), float(self.increment_entry.text()))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = InventoryApp()
    main_win.show()
    sys.exit(app.exec_())
