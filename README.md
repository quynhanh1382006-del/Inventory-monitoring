# PHỤ LỤC: HƯỚNG DẪN CÀI ĐẶT, ĐĂNG NHẬP VÀ SỬ DỤNG HỆ THỐNG GIÁM SÁT KHO HÀNG

## 1. Giới thiệu

Hệ thống Inventory Monitoring được xây dựng nhằm quản lý kho hàng và theo dõi tình trạng hoạt động của hệ thống thông qua các công cụ giám sát. Hệ thống sử dụng Docker Compose để triển khai các dịch vụ gồm ứng dụng web, MySQL, Prometheus, Grafana và Node Exporter.

## 2. Các thành phần của hệ thống

| Thành phần | Chức năng | Địa chỉ khi chạy trên máy triển khai |
|---|---|---|
| Giao diện web | Đăng nhập, quản lý kho hàng, xem thống kê | http://localhost:5000 |
| Grafana | Hiển thị dashboard giám sát | http://localhost:3000 |
| Prometheus | Truy vấn và kiểm tra các chỉ số giám sát | http://localhost:9090 |
| Node Exporter | Cung cấp chỉ số CPU, bộ nhớ, ổ đĩa và hệ thống | http://localhost:9100/metrics |
| MySQL | Lưu trữ dữ liệu của hệ thống | Cổng 3306, không truy cập trực tiếp qua trình duyệt |

**Lưu ý:** Các địa chỉ trên sử dụng `localhost`, vì vậy chỉ truy cập trực tiếp được trên máy đang triển khai hệ thống. Khi cung cấp cho giảng viên sử dụng từ xa, cần thay bằng địa chỉ truy cập công khai đã được cấu hình và kiểm tra.

## 3. Hướng dẫn khởi động hệ thống

Bước 1: Mở Ubuntu và truy cập thư mục dự án:

```bash
cd ~/inventory-monitoring
```

Bước 2: Khởi động các dịch vụ:

```bash
docker compose up -d
```

Bước 3: Kiểm tra trạng thái:

```bash
docker compose ps
```

Đảm bảo các dịch vụ `app`, `mysql`, `grafana`, `prometheus` và `node-exporter` đang hoạt động.

Bước 4: Mở giao diện web tại `http://localhost:5000`.

## 4. Hướng dẫn đăng nhập và đăng ký

1. Mở giao diện web của hệ thống.
2. Nhập tên tài khoản và mật khẩu đã đăng ký.
3. Nhấn nút đăng nhập để truy cập giao diện quản lý kho hàng.
4. Nếu chưa có tài khoản, chọn chức năng đăng ký và nhập các thông tin được yêu cầu.
5. Sau khi đăng nhập thành công, người dùng có thể sử dụng các chức năng quản lý kho được cung cấp trên giao diện.
6. Khi sử dụng xong, nhấn nút **Đăng xuất**.

Tài khoản trình diễn dành cho giảng viên cần được tạo trước khi bàn giao. Không ghi mật khẩu cá nhân hoặc thông tin xác thực nhạy cảm trực tiếp trong báo cáo công khai.

## 5. Hướng dẫn sử dụng Grafana

1. Mở `http://localhost:3000`.
2. Đăng nhập bằng tài khoản Grafana đã được cấu hình.
3. Mở dashboard giám sát đã tạo.
4. Quan sát các biểu đồ và chỉ số hệ thống được hiển thị.
5. Nếu dashboard chưa có dữ liệu, kiểm tra trạng thái Prometheus và nguồn dữ liệu của Grafana.

## 6. Hướng dẫn sử dụng Prometheus

1. Mở `http://localhost:9090`.
2. Truy cập trang Graph.
3. Nhập tên chỉ số cần kiểm tra vào ô truy vấn.
4. Nhấn Execute để thực hiện truy vấn.
5. Quan sát kết quả dưới dạng bảng hoặc biểu đồ.

Có thể mở mục Status → Targets để kiểm tra các mục tiêu giám sát và trạng thái thu thập dữ liệu.

## 7. Kiểm tra Node Exporter

Truy cập `http://localhost:9100/metrics` để xem các chỉ số dạng văn bản do Node Exporter cung cấp. Prometheus sử dụng các chỉ số này để thu thập và phục vụ việc giám sát tài nguyên hệ thống.

## 8. Tắt và khởi động lại hệ thống

Để dừng các dịch vụ mà không xóa dữ liệu lưu trữ:

```bash
cd ~/inventory-monitoring
docker compose stop
```

Để khởi động lại:

```bash
docker compose up -d
```

Không sử dụng lệnh `docker compose down -v` trong quá trình sử dụng thông thường vì lệnh này có thể xóa các volume chứa dữ liệu.

## 9. Mã nguồn dự án

Mã nguồn được lưu trữ tại repository GitHub của dự án. Repository bao gồm mã ứng dụng, cấu hình Docker Compose và cấu hình giám sát cần thiết để triển khai hệ thống.

Đường dẫn repository: **Bổ sung sau khi xác nhận URL GitHub chính thức.**

## 10. Kết luận

Phụ lục cung cấp các bước cơ bản để khởi động hệ thống, đăng nhập, sử dụng giao diện quản lý kho hàng và kiểm tra hoạt động của các thành phần giám sát. Người sử dụng cần bảo vệ thông tin đăng nhập và bảo đảm các dịch vụ được cấu hình an toàn trước khi công khai truy cập từ Internet.

