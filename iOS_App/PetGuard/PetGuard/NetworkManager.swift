//
//  NetworkManager.swift
//  PetGuard
//
//  Created by Tsz Chiu Ng  on 19/12/2025.
//  Handles communication with Python backend server

import Foundation
import UIKit
import UserNotifications

class NetworkManager: ObservableObject {
    // MARK: - Published Properties
    @Published var isConnected = false
    @Published var isRecording = false
    @Published var currentVideo: String?
    @Published var detections: [Detection] = []
    @Published var videos: [VideoInfo] = []
    @Published var proximityAlert = false
    @Published var beaconDistance: Double = 999.0
    
    // MARK: - Configuration
    // Change this to your Mac/Jetson IP address
    private(set) var baseURL = "http://172.20.10.3:5001"
    
    // Find your device's IP by running: ipconfig getifaddr en0
    // Then update like: "http://172.20.10.3:5001"
    // Server runs on port 5001
    
    func updateServerURL(_ url: String) {
        self.baseURL = url
    }
    
    // MARK: - Fetch Live Stream Frame
    func fetchLiveFrame(completion: @escaping (UIImage?) -> Void) {
        guard let url = URL(string: "\(baseURL)/stream/live") else {
            completion(nil)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 2
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self, let data = data, error == nil else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let streamResponse = try decoder.decode(StreamResponse.self, from: data)
                
                // Decode base64 image
                if let imageData = Data(base64Encoded: streamResponse.frame) {
                    let image = UIImage(data: imageData)
                    
                    DispatchQueue.main.async {
                        self.detections = streamResponse.detections
                        self.isRecording = streamResponse.isRecording
                        self.currentVideo = streamResponse.currentVideo
                        
                        // Handle proximity alert
                        let wasAlert = self.proximityAlert
                        self.proximityAlert = streamResponse.proximityAlert ?? false
                        self.beaconDistance = streamResponse.beaconDistance ?? 999.0
                        
                        // Trigger notification if alert just activated
                        if self.proximityAlert && !wasAlert {
                            self.sendProximityNotification()
                        }
                        
                        completion(image)
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(nil)
                    }
                }
            } catch {
                print("Decoding error: \(error)")
                DispatchQueue.main.async {
                    completion(nil)
                }
            }
        }.resume()
    }
    
    struct StreamResponse: Codable {
        let frame: String
        let detections: [Detection]
        let isRecording: Bool
        let currentVideo: String?
        let proximityAlert: Bool?
        let beaconDistance: Double?
        let timestamp: String
        
        enum CodingKeys: String, CodingKey {
            case frame, detections, timestamp
            case isRecording = "is_recording"
            case currentVideo = "current_video"
            case proximityAlert = "proximity_alert"
            case beaconDistance = "beacon_distance"
        }
    }
    
    // MARK: - Detection Models
    struct Detection: Codable, Identifiable {
        let id = UUID()
        let className: String
        let confidence: Double
        let bbox: [Double]
        
        enum CodingKeys: String, CodingKey {
            case className = "class"
            case confidence
            case bbox
        }
    }
    
    struct DetectionResponse: Codable {
        let detections: [Detection]
        let hasHuman: Bool
        let hasCat: Bool
        let bothDetected: Bool
        let isRecording: Bool
        let currentVideo: String?
        let timestamp: String
        
        enum CodingKeys: String, CodingKey {
            case detections
            case hasHuman = "has_human"
            case hasCat = "has_cat"
            case bothDetected = "both_detected"
            case isRecording = "is_recording"
            case currentVideo = "current_video"
            case timestamp
        }
    }
    
    struct VideoInfo: Codable, Identifiable {
        let id = UUID()
        let filename: String
        let size: Int
        let created: String
        let url: String
        
        enum CodingKeys: String, CodingKey {
            case filename, size, created, url
        }
    }
    
    struct VideosResponse: Codable {
        let videos: [VideoInfo]
        let count: Int
    }
    
    // MARK: - Health Check
    func checkHealth(completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(baseURL)/health") else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 5
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                if error == nil, let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    self?.isConnected = true
                    completion(true)
                } else {
                    self?.isConnected = false
                    completion(false)
                }
            }
        }.resume()
    }
    
    // MARK: - Send Frame for Detection
    func sendFrame(_ image: UIImage, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(baseURL)/detect") else {
            completion(false)
            return
        }
        
        // Convert image to JPEG data
        guard let imageData = image.jpegData(compressionQuality: 0.7) else {
            completion(false)
            return
        }
        
        // Convert to base64
        let base64String = imageData.base64EncodedString()
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10
        
        let body: [String: Any] = ["frame": base64String]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        } catch {
            print("Error encoding frame: \(error)")
            completion(false)
            return
        }
        
        // Send request
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else { return }
            
            if let error = error {
                print("Network error: \(error.localizedDescription)")
                DispatchQueue.main.async {
                    completion(false)
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(false)
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let response = try decoder.decode(DetectionResponse.self, from: data)
                
                DispatchQueue.main.async {
                    self.detections = response.detections
                    self.isRecording = response.isRecording
                    self.currentVideo = response.currentVideo
                    completion(true)
                }
            } catch {
                print("Decoding error: \(error)")
                DispatchQueue.main.async {
                    completion(false)
                }
            }
        }.resume()
    }
    
    // MARK: - Fetch Videos List
    func fetchVideos(completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(baseURL)/videos") else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self, let data = data, error == nil else {
                DispatchQueue.main.async {
                    completion(false)
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let response = try decoder.decode(VideosResponse.self, from: data)
                
                DispatchQueue.main.async {
                    self.videos = response.videos
                    completion(true)
                }
            } catch {
                print("Decoding error: \(error)")
                DispatchQueue.main.async {
                    completion(false)
                }
            }
        }.resume()
    }
    
    // MARK: - Download Video
    func downloadVideo(filename: String, completion: @escaping (URL?) -> Void) {
        guard let url = URL(string: "\(baseURL)/videos/\(filename)") else {
            completion(nil)
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data, error == nil else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Save to temporary file
            let tempURL = FileManager.default.temporaryDirectory
                .appendingPathComponent(filename)
            
            do {
                try data.write(to: tempURL)
                DispatchQueue.main.async {
                    completion(tempURL)
                }
            } catch {
                print("Error saving video: \(error)")
                DispatchQueue.main.async {
                    completion(nil)
                }
            }
        }.resume()
    }
    
    // MARK: - Delete Video
    func deleteVideo(filename: String, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(baseURL)/videos/\(filename)") else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if error == nil, let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    completion(true)
                } else {
                    completion(false)
                }
            }
        }.resume()
    }
    
    // MARK: - Get Video URL
    func getVideoURL(filename: String) -> URL? {
        return URL(string: "\(baseURL)/videos/\(filename)")
    }
    
    // MARK: - Proximity Notification
    func sendProximityNotification() {
        let content = UNMutableNotificationContent()
        content.title = "Warning!"
        content.body = "Someone is too close to the area! Check the camera now!"
        content.sound = .default
        content.badge = 1
        
        // Trigger immediately
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: trigger)
        
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("❌ Notification error: \(error.localizedDescription)")
            } else {
                print("✅ Proximity notification sent")
            }
        }
    }
}
