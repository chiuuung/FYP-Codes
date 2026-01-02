/*
 * ESP32-S3 Camera + BLE Beacon Proximity Detection (OPTIMIZED)
 * 
 * Streams camera to Mac backend + detects BLE beacon proximity
 * BLE runs on separate core to prevent camera lag
 * 
 * Hardware: ESP32-S3 with OV5640 5MP camera
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// ==================== CONFIGURATION ====================

// WiFi Settings
const char* ssid = "Chiu😺";
const char* password = "james5123";

// Mac Backend Server
const char* serverIP = "172.20.10.3";
const int serverPort = 5001;

// BLE Beacon Settings
const char* TARGET_BEACON_MAC = "5208240800d1";
const int RSSI_THRESHOLD_1M = -70;  // >= -70 means within 1m

// Camera Pins - ESP32-S3 WROVER CAM
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     15
#define SIOD_GPIO_NUM     4
#define SIOC_GPIO_NUM     5
#define Y9_GPIO_NUM       16
#define Y8_GPIO_NUM       17
#define Y7_GPIO_NUM       18
#define Y6_GPIO_NUM       12
#define Y5_GPIO_NUM       10
#define Y4_GPIO_NUM       8
#define Y3_GPIO_NUM       9
#define Y2_GPIO_NUM       11
#define VSYNC_GPIO_NUM    6
#define HREF_GPIO_NUM     7
#define PCLK_GPIO_NUM     13

// Camera Settings
#define FRAME_SIZE FRAMESIZE_VGA
#define STREAM_FPS 10
unsigned long lastFrameTime = 0;
int frameDelay = 1000 / STREAM_FPS;

// BLE State (shared between cores)
volatile int beaconRSSI = -100;
volatile bool beaconFound = false;
volatile unsigned long lastBeaconTime = 0;

// HTTP Server
httpd_handle_t stream_httpd = NULL;

// ==================== CAMERA INITIALIZATION ====================

bool initCamera() {
  Serial.println("📷 Initializing camera...");
  
  if (!psramFound()) {
    Serial.println("❌ ERROR: PSRAM not found!");
    return false;
  }
  Serial.printf("✅ PSRAM: %d bytes\n", ESP.getPsramSize());
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAME_SIZE;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 10;
  config.fb_count = 2;
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    return false;
  }
  
  sensor_t * s = esp_camera_sensor_get();
  if (s == NULL) {
    Serial.println("❌ Failed to get camera sensor");
    return false;
  }
  
  // Optimized settings for AI detection
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);
  s->set_saturation(s, 1);
  s->set_special_effect(s, 0);
  s->set_whitebal(s, 1);
  s->set_awb_gain(s, 1);
  s->set_wb_mode(s, 0);
  s->set_exposure_ctrl(s, 1);
  s->set_aec2(s, 1);
  s->set_ae_level(s, 1);
  s->set_aec_value(s, 400);
  s->set_gain_ctrl(s, 1);
  s->set_agc_gain(s, 5);
  s->set_gainceiling(s, (gainceiling_t)2);
  s->set_bpc(s, 1);
  s->set_wpc(s, 1);
  s->set_raw_gma(s, 1);
  s->set_lenc(s, 1);
  s->set_hmirror(s, 0);
  s->set_vflip(s, 0);
  s->set_dcw(s, 1);
  s->set_colorbar(s, 0);
  s->set_sharpness(s, 2);
  
  Serial.println("✅ Camera initialized!");
  return true;
}

// ==================== MJPEG STREAM ====================

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];

  res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
  if (res != ESP_OK) return res;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      res = ESP_FAIL;
    } else {
      if (fb->format != PIXFORMAT_JPEG) {
        bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
        esp_camera_fb_return(fb);
        fb = NULL;
        if (!jpeg_converted) res = ESP_FAIL;
      } else {
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
      }
    }
    
    if (res == ESP_OK) {
      size_t hlen = snprintf((char *)part_buf, 64, 
        "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", _jpg_buf_len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    }
    
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, "\r\n", 2);
    }
    
    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }
    
    if (res != ESP_OK) break;
  }
  
  return res;
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;

  httpd_uri_t stream_uri = {
    .uri = "/stream",
    .method = HTTP_GET,
    .handler = stream_handler,
    .user_ctx = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("✅ Streaming server started!");
  }
}

// ==================== BLE SCANNING (CORE 0) ====================

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {
    String macAddress = advertisedDevice.getAddress().toString().c_str();
    macAddress.toLowerCase();
    macAddress.replace(":", "");
    
    String targetMac = String(TARGET_BEACON_MAC);
    targetMac.toLowerCase();
    
    if (macAddress == targetMac) {
      beaconRSSI = advertisedDevice.getRSSI();
      beaconFound = true;
      lastBeaconTime = millis();
      
      bool isClose = (beaconRSSI >= RSSI_THRESHOLD_1M);
      Serial.printf("📡 Beacon RSSI: %d dBm | %s\n", 
                    beaconRSSI, 
                    isClose ? "✅ WITHIN 1M" : "❌ BEYOND 1M");
    }
  }
};

BLEScan* pBLEScan;

void bleScanTask(void * parameter) {
  // Initialize BLE on Core 0
  BLEDevice::init("ESP32-S3-Camera");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);
  
  Serial.println("✅ BLE scanner started on Core 0");
  
  while(true) {
    // Scan for 1 second
    pBLEScan->start(1, false);
    pBLEScan->clearResults();
    
    // Check if beacon is stale (no update for 3 seconds)
    if (millis() - lastBeaconTime > 3000) {
      beaconFound = false;
      beaconRSSI = -100;
    }
    
    delay(1000);  // Scan every 1 second
  }
}

// ==================== SEND FRAME TO MAC ====================

void sendFrameToMac() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Camera capture failed");
    return;
  }

  HTTPClient http;
  String url = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/frame";
  
  http.begin(url);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Device", "ESP32-S3");
  http.setTimeout(3000);
  
  int httpCode = http.POST(fb->buf, fb->len);
  
  if (httpCode != 200 && httpCode > 0) {
    Serial.printf("⚠️  Frame HTTP: %d\n", httpCode);
  }
  
  http.end();
  esp_camera_fb_return(fb);
}

void sendDistanceToMac() {
  if (!beaconFound) {
    return;  // No beacon data to send
  }
  
  HTTPClient http;
  String url = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/distance";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(2000);
  
  // Calculate simple distance
  float distance = (beaconRSSI >= RSSI_THRESHOLD_1M) ? 0.5 : 1.5;
  
  String json = "{";
  json += "\"rssi\":" + String(beaconRSSI) + ",";
  json += "\"distance\":" + String(distance, 2) + ",";
  json += "\"beacon_mac\":\"" + String(TARGET_BEACON_MAC) + "\"";
  json += "}";
  
  int httpCode = http.POST(json);
  
  if (httpCode == 200) {
    Serial.printf("✅ Distance sent: %.2fm (RSSI: %d)\n", distance, beaconRSSI);
  } else if (httpCode > 0) {
    Serial.printf("⚠️  Distance HTTP: %d\n", httpCode);
  }
  
  http.end();
}

// ==================== SETUP ====================

void setup() {
  Serial.begin(115200);
  Serial.println("\n🚀 ESP32-S3 Camera + BLE Beacon Scanner");
  Serial.println("==========================================");
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("❌ Camera initialization failed!");
    while (1) delay(1000);
  }
  
  // Connect WiFi
  Serial.printf("📡 Connecting to WiFi: %s\n", ssid);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.printf("📍 ESP32 IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("🖥️  Backend: http://%s:%d\n", serverIP, serverPort);
    
    startCameraServer();
    
    // Start BLE scanning on Core 0 (camera uses Core 1)
    xTaskCreatePinnedToCore(
      bleScanTask,
      "BLE_Scan",
      4096,
      NULL,
      1,
      NULL,
      0  // Core 0
    );
    
    Serial.println("\n🎉 Setup complete!");
    Serial.println("📺 Stream: http://" + WiFi.localIP().toString() + "/stream");
    Serial.println("🔄 FPS: " + String(STREAM_FPS));
    Serial.println("🔵 BLE: Scanning on Core 0");
    Serial.println("==========================================\n");
  } else {
    Serial.println("\n❌ WiFi failed!");
  }
}

// ==================== MAIN LOOP (CORE 1) ====================

unsigned long lastDistanceSend = 0;

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.begin(ssid, password);
    delay(5000);
    return;
  }
  
  unsigned long currentTime = millis();
  
  // Send camera frame at controlled rate (10 FPS)
  if (currentTime - lastFrameTime >= frameDelay) {
    lastFrameTime = currentTime;
    sendFrameToMac();
  }
  
  // Send distance data every 1 second
  if (currentTime - lastDistanceSend >= 1000) {
    lastDistanceSend = currentTime;
    sendDistanceToMac();
  }
  
  delay(10);
}
