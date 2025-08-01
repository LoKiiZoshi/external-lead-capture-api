# Generated by Django 5.2.3 on 2025-07-29 08:20

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')], default='active', max_length=20)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('blacklisted', 'Blacklisted')], default='active', max_length=20)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('sku', models.CharField(help_text='Stock Keeping Unit', max_length=50, unique=True)),
                ('product_type', models.CharField(choices=[('fresh', 'Fresh Produce'), ('frozen', 'Frozen'), ('dry_goods', 'Dry Goods'), ('beverages', 'Beverages'), ('condiments', 'Condiments & Spices'), ('meat', 'Meat & Poultry'), ('seafood', 'Seafood'), ('dairy', 'Dairy Products'), ('other', 'Other')], default='other', max_length=20)),
                ('unit_of_measure', models.CharField(choices=[('kg', 'Kilograms'), ('g', 'Grams'), ('l', 'Liters'), ('ml', 'Milliliters'), ('piece', 'Pieces'), ('dozen', 'Dozen'), ('pack', 'Pack'), ('box', 'Box'), ('bag', 'Bag'), ('bottle', 'Bottle'), ('can', 'Can')], default='piece', max_length=20)),
                ('cost_per_unit', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('minimum_stock_level', models.DecimalField(decimal_places=2, default=0, help_text='Minimum quantity before reorder alert', max_digits=10)),
                ('maximum_stock_level', models.DecimalField(blank=True, decimal_places=2, help_text='Maximum storage capacity', max_digits=10, null=True)),
                ('shelf_life_days', models.PositiveIntegerField(blank=True, help_text='Shelf life in days', null=True)),
                ('storage_instructions', models.TextField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('discontinued', 'Discontinued'), ('seasonal', 'Seasonal'), ('out_of_stock', 'Out of Stock')], default='active', max_length=20)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='stockmanagement.category')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='stockmanagement.supplier')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StockEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch_number', models.CharField(blank=True, max_length=100)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('entry_type', models.CharField(choices=[('purchase', 'Purchase'), ('return', 'Return from Kitchen'), ('adjustment', 'Stock Adjustment'), ('transfer', 'Transfer'), ('waste', 'Waste/Spoilage')], default='purchase', max_length=20)),
                ('status', models.CharField(choices=[('available', 'Available'), ('reserved', 'Reserved'), ('expired', 'Expired'), ('damaged', 'Damaged'), ('used', 'Used'), ('returned', 'Returned to Supplier')], default='available', max_length=20)),
                ('received_date', models.DateTimeField(auto_now_add=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('cost_per_unit', models.DecimalField(decimal_places=2, help_text='Cost per unit for this specific entry', max_digits=10)),
                ('reference_number', models.CharField(blank=True, help_text='Invoice number, PO number, etc.', max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_entries', to='stockmanagement.product')),
            ],
            options={
                'verbose_name_plural': 'Stock Entries',
                'ordering': ['-received_date'],
            },
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('movement_type', models.CharField(choices=[('in', 'Stock In'), ('out', 'Stock Out'), ('adjustment', 'Adjustment'), ('transfer', 'Transfer'), ('waste', 'Waste')], max_length=20)),
                ('quantity_changed', models.DecimalField(decimal_places=2, help_text='Positive for increases, negative for decreases', max_digits=10)),
                ('previous_quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('new_quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.CharField(blank=True, max_length=200)),
                ('performed_by', models.CharField(blank=True, max_length=100)),
                ('reference_document', models.CharField(blank=True, max_length=100)),
                ('stock_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='stockmanagement.stockentry')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='stockentry',
            index=models.Index(fields=['product', 'status'], name='stockmanage_product_ec2a34_idx'),
        ),
        migrations.AddIndex(
            model_name='stockentry',
            index=models.Index(fields=['expiry_date'], name='stockmanage_expiry__72edb2_idx'),
        ),
        migrations.AddIndex(
            model_name='stockentry',
            index=models.Index(fields=['batch_number'], name='stockmanage_batch_n_e2966f_idx'),
        ),
        migrations.AddIndex(
            model_name='stockmovement',
            index=models.Index(fields=['stock_entry', 'movement_type'], name='stockmanage_stock_e_93ccd1_idx'),
        ),
        migrations.AddIndex(
            model_name='stockmovement',
            index=models.Index(fields=['created_at'], name='stockmanage_created_99072b_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sku'], name='stockmanage_sku_a5857c_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'status'], name='stockmanage_categor_9a1a86_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['product_type'], name='stockmanage_product_a4cb94_idx'),
        ),
    ]
