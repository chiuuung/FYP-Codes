//
//  StreamView.swift
//  PetGuard
//
//  Created by Tsz Chiu Ng  on 19/12/2025.
//  Displays live stream from Mac/Jetson camera
//  NO iPhone camera needed - just viewing!

import SwiftUI

struct StreamView: View {
    @ObservedObject var networkManager: NetworkManager
    
    @State private var streamImage: UIImage?
    @State private var isLoadingStream = false
    @State private var showingSettings = false
    @State private var streamTimer: Timer?
    @State private var showProximityAlert = false
    
    var body: some View {
        ZStack {
            // Stream display
            if let image = streamImage {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .ignoresSafeArea()
            } else {
                // No stream placeholder
                VStack(spacing: 20) {
                    Image(systemName: "video.slash")
                        .font(.system(size: 60))
                        .foregroundColor(.gray)
                    
                    Text("No Stream Available")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    if isLoadingStream {
                        ProgressView()
                            .scaleEffect(1.5)
                            .padding()
                    }
                    
                    Text("Make sure the server is running on your Mac/Jetson")
                        .font(.caption)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }
            }
            
            // Overlay UI
            VStack {
                // Top bar
                HStack {
                    // Connection status
                    HStack(spacing: 8) {
                        Circle()
                            .fill(networkManager.isConnected ? Color.green : Color.red)
                            .frame(width: 12, height: 12)
                        
                        Text(networkManager.isConnected ? "Connected" : "Disconnected")
                            .font(.caption)
                            .foregroundColor(.white)
                    }
                    .padding(8)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(8)
                    
                    Spacer()
                    
                    // Proximity alert indicator
                    if networkManager.proximityAlert {
                        HStack(spacing: 8) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.white)
                            
                            Text("PROXIMITY ALERT")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.white)
                        }
                        .padding(8)
                        .background(Color.orange.opacity(0.9))
                        .cornerRadius(8)
                    }
                    
                    // Recording indicator
                    if networkManager.isRecording {
                        HStack(spacing: 8) {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 12, height: 12)
                            
                            Text("RECORDING")
                                .font(.caption)
                                .fontWeight(.bold)
                                .foregroundColor(.white)
                        }
                        .padding(8)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(8)
                    }
                    
                    // Settings button
                    Button(action: {
                        showingSettings = true
                    }) {
                        Image(systemName: "gear")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding(8)
                            .background(Color.black.opacity(0.6))
                            .cornerRadius(8)
                    }
                }
                .padding()
                
                Spacer()
                
                // Detection info
                VStack(spacing: 12) {
                    ForEach(networkManager.detections) { detection in
                        HStack {
                            Image(systemName: detection.className == "human" ? "person.fill" : "pawprint.fill")
                                .foregroundColor(.white)
                            
                            Text(detection.className.capitalized)
                                .foregroundColor(.white)
                                .fontWeight(.semibold)
                            
                            Spacer()
                            
                            Text(String(format: "%.1f%%", detection.confidence * 100))
                                .foregroundColor(.white)
                                .font(.caption)
                        }
                        .padding(12)
                        .background(detection.className == "human" ? Color.blue.opacity(0.7) : Color.orange.opacity(0.7))
                        .cornerRadius(8)
                    }
                }
                .padding()
            }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView(
                networkManager: networkManager
            )
        }
        .alert("Warning!", isPresented: $showProximityAlert) {
            Button("OK", role: .cancel) { }
        } message: {
            Text("Someone too close to the area! Check the camera now!")
        }
        .onAppear {
            startStreaming()
            networkManager.checkHealth { _ in }
        }
        .onDisappear {
            stopStreaming()
        }
        .onChange(of: networkManager.proximityAlert) { newValue in
            if newValue {
                showProximityAlert = true
            }
        }
    }
    
    func startStreaming() {
        isLoadingStream = true
        
        // Poll for frames every 100ms (~10 FPS)
        streamTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            fetchLatestFrame()
        }
    }
    
    func stopStreaming() {
        streamTimer?.invalidate()
        streamTimer = nil
        isLoadingStream = false
    }
    
    func fetchLatestFrame() {
        networkManager.fetchLiveFrame { image in
            if let image = image {
                self.streamImage = image
                self.isLoadingStream = false
            }
        }
    }
}

// MARK: - Settings View
struct SettingsView: View {
    @ObservedObject var networkManager: NetworkManager
    
    @Environment(\.dismiss) var dismiss
    @State private var tempURL: String = ""
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Server Configuration")) {
                    TextField("Server URL", text: $tempURL)
                        .autocapitalization(.none)
                        .keyboardType(.URL)
                    
                    Button("Test Connection") {
                        networkManager.updateServerURL(tempURL)
                        networkManager.checkHealth { success in
                            alertMessage = success ? "✅ Connected successfully!" : "❌ Connection failed. Check URL and server."
                            showingAlert = true
                        }
                    }
                    .foregroundColor(.blue)
                    
                    HStack {
                        Text("Status:")
                        Spacer()
                        Text(networkManager.isConnected ? "Connected" : "Disconnected")
                            .foregroundColor(networkManager.isConnected ? .green : .red)
                    }
                }
                
                    // ...existing code...
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .alert("Connection Test", isPresented: $showingAlert) {
                Button("OK", role: .cancel) { }
            } message: {
                Text(alertMessage)
            }
            .onAppear {
                tempURL = networkManager.baseURL
            }
        }
    }
}

struct StreamView_Previews: PreviewProvider {
    static var previews: some View {
        StreamView(networkManager: NetworkManager())
    }
}
