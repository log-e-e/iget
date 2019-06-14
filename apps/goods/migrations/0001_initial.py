# Generated by Django 2.1.7 on 2019-05-10 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='名称')),
                ('price', models.IntegerField(default=0, verbose_name='价格')),
                ('buy_link', models.CharField(max_length=254, unique=True, verbose_name='购买链接')),
                ('prd_serial_number', models.CharField(max_length=254, unique=True, verbose_name='所属产品编号')),
                ('mall_id', models.IntegerField(verbose_name='所属商城')),
                ('status', models.IntegerField(choices=[(-1, '已下架'), (0, '在售')], default=0, verbose_name='商品状态')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
                'ordering': ['prd_serial_number'],
            },
        ),
        migrations.CreateModel(
            name='Mall',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='官网名称')),
                ('official_link', models.CharField(max_length=200, unique=True, verbose_name='官网链接')),
                ('status', models.IntegerField(choices=[(-1, '停止服务'), (0, '服务中')], default=0, verbose_name='商城状态')),
            ],
            options={
                'verbose_name': '商城',
                'verbose_name_plural': '商城',
                'ordering': ['name'],
            },
        ),
    ]