//
//  VideosView.swift
//  PetGuard
//
//  Created by Tsz Chiu Ng  on 19/12/2025.
//  View to browse and play recorded videos

import SwiftUI
import AVKit

struct VideosView: View {
    @ObservedObject var networkManager: NetworkManager
    
    @State private var isLoading = false
    @State private var selectedVideo: NetworkManager.VideoInfo?
    @State private var showingPlayer = false
    @State private var videoURL: URL?
    
    var body: some View {
        NavigationView {
            Group {
                if networkManager.videos.isEmpty && !isLoading {
                    // Empty state
                    VStack(spacing: 20) {
                        Image(systemName: "video.slash")
                            .font(.system(size: 60))
                            .foregroundColor(.gray)
                        
                        Text("No Videos Yet")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("Videos will appear here when cat and human are detected together")
                            .font(.body)
                            .foregroundColor(.gray)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 40)
                        
                        Button(action: refreshVideos) {
                            HStack {
                                Image(systemName: "arrow.clockwise")
                                Text("Refresh")
                            }
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                        }
                        .padding(.top)
                    }
                } else {
                    // Video list
                    List {
                        ForEach(networkManager.videos) { video in
                            VideoRow(video: video)
                                .contentShape(Rectangle())
                                .onTapGesture {
                                    playVideo(video)
                                }
                                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                                    Button(role: .destructive) {
                                        deleteVideo(video)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                }
                        }
                    }
                    .refreshable {
                        refreshVideos()
                    }
                }
            }
            .navigationTitle("Recorded Videos")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: refreshVideos) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .disabled(isLoading)
                }
            }
            .overlay {
                if isLoading {
                    ProgressView()
                        .scaleEffect(1.5)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(Color.black.opacity(0.2))
                }
            }
            .sheet(isPresented: $showingPlayer) {
                if let url = videoURL {
                    VideoPlayerView(url: url, videoName: selectedVideo?.filename ?? "Video")
                }
            }
        }
        .onAppear {
            refreshVideos()
        }
    }
    
    // MARK: - Actions
    func refreshVideos() {
        isLoading = true
        networkManager.fetchVideos { success in
            isLoading = false
            if !success {
                print("Failed to fetch videos")
            }
        }
    }
    
    func playVideo(_ video: NetworkManager.VideoInfo) {
        isLoading = true
        selectedVideo = video
        
        networkManager.downloadVideo(filename: video.filename) { url in
            isLoading = false
            if let url = url {
                self.videoURL = url
                self.showingPlayer = true
            } else {
                print("Failed to download video")
            }
        }
    }
    
    func deleteVideo(_ video: NetworkManager.VideoInfo) {
        networkManager.deleteVideo(filename: video.filename) { success in
            if success {
                refreshVideos()
            } else {
                print("Failed to delete video")
            }
        }
    }
}

// MARK: - Video Row
struct VideoRow: View {
    let video: NetworkManager.VideoInfo
    
    var body: some View {
        HStack(spacing: 15) {
            // Thumbnail
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 80, height: 60)
                
                Image(systemName: "play.circle.fill")
                    .font(.system(size: 30))
                    .foregroundColor(.white)
            }
            
            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(formatFilename(video.filename))
                    .font(.headline)
                
                Text(formatDate(video.created))
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Text(formatSize(video.size))
                    .font(.caption)
                    .foregroundColor(.gray)
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .foregroundColor(.gray)
                .font(.caption)
        }
        .padding(.vertical, 8)
    }
    
    func formatFilename(_ filename: String) -> String {
        return filename
            .replacingOccurrences(of: "interaction_", with: "")
            .replacingOccurrences(of: ".mp4", with: "")
            .replacingOccurrences(of: "_", with: " ")
    }
    
    func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        return dateString
    }
    
    func formatSize(_ bytes: Int) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useMB, .useKB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }
}

// MARK: - Video Player View
struct VideoPlayerView: View {
    let url: URL
    let videoName: String
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            VideoPlayer(player: AVPlayer(url: url))
                .navigationTitle(videoName)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Done") {
                            dismiss()
                        }
                    }
                }
        }
        .onAppear {
            // Auto-play
            if let player = AVPlayer(url: url) as AVPlayer? {
                player.play()
            }
        }
    }
}

// MARK: - Preview
struct VideosView_Previews: PreviewProvider {
    static var previews: some View {
        VideosView(networkManager: NetworkManager())
    }
}
