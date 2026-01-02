//
//  ContentView.swift
//  PetGuard
//
//  Created by Tsz Chiu Ng  on 19/12/2025.
//  Main app view with tab navigation

import SwiftUI

struct ContentView: View {
    @StateObject private var networkManager = NetworkManager()
    
    var body: some View {
        TabView {
            StreamView(networkManager: networkManager)
                .tabItem {
                    Label("Live Stream", systemImage: "video.fill")
                }
            
            // ARDUINO MOTOR CONTROL - Commented out (see arduino_motor_control folder)
            // Uncomment this when you add ControlView.swift to your Xcode project
            /*
            ControlView()
                .tabItem {
                    Label("Control", systemImage: "gamecontroller.fill")
                }
            */
            
            VideosView(networkManager: networkManager)
                .tabItem {
                    Label("Recordings", systemImage: "film.fill")
                }
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

