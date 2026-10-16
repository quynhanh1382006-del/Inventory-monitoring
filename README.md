# Inventory Monitoring System

Hệ thống Quản lý Kho hàng (Inventory) tích hợp giám sát hệ thống bằng:

- Spring Boot
- MySQL
- Docker
- Docker Compose
- Prometheus
- Node Exporter
- Grafana

## Mục tiêu

Xây dựng hệ thống quản lý kho hàng và giám sát hiệu năng máy chủ trên Ubuntu Server.

## Monitoring

Hệ thống theo dõi:

- CPU
- RAM
- Disk
- Disk I/O
- Network
- System Load

## Architecture

Inventory Application
→ MySQL

Ubuntu Server
→ Node Exporter
→ Prometheus
→ Grafana
