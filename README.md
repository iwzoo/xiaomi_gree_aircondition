# Xiaomi AC Partner with Gree Air Condition

Home Assistant+米家空调伴侣 遥控器型号为YAP0FB2的格力空调 （有Ey易享模式的空调）

基于 https://github.com/syssi/xiaomi_airconditioningcompanion


在configuration.yaml中添加

```
climate:
  - platform: xiaomi_miio_gree
    name: Gree AC
    host: 192.168.10.12
    token: 【token】
    target_sensor: sensor.temperature_158d0001f53706 #温度传感器
    scan_interval: 10
```    
