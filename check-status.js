#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

console.log('🔍 VFX Folder Normalizer - Status Check');
console.log('='.repeat(50));

// Check if required files exist
const requiredFiles = [
    'package.json',
    'dist/main.js',
    'dist/preload.js',
    'python/normalizer.py',
    'src/main.tsx'
];

console.log('\n📁 Checking required files...');
requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`✅ ${file}`);
    } else {
        console.log(`❌ ${file} - MISSING`);
    }
});

// Check if Vite dev server is running
console.log('\n🌐 Checking development servers...');
const http = require('http');

function checkPort(port, name) {
    return new Promise((resolve) => {
        const req = http.request({
            hostname: 'localhost',
            port: port,
            method: 'GET',
            timeout: 1000
        }, (res) => {
            console.log(`✅ ${name} running on port ${port}`);
            resolve(true);
        });
        
        req.on('error', () => {
            console.log(`❌ ${name} not running on port ${port}`);
            resolve(false);
        });
        
        req.on('timeout', () => {
            console.log(`❌ ${name} timeout on port ${port}`);
            resolve(false);
        });
        
        req.end();
    });
}

async function checkServers() {
    await checkPort(3000, 'Vite Dev Server (port 3000)');
    await checkPort(3001, 'Vite Dev Server (port 3001)');
    
    console.log('\n🐍 Testing Python backend...');
    
    const pythonTest = spawn('py', ['-c', 'import python.normalizer; print("Python OK")'], {
        stdio: 'pipe'
    });
    
    pythonTest.stdout.on('data', (data) => {
        console.log('✅ Python backend: WORKING');
    });
    
    pythonTest.stderr.on('data', (data) => {
        console.log('❌ Python backend error:', data.toString());
    });
    
    pythonTest.on('close', (code) => {
        if (code === 0) {
            console.log('\n🎉 Status check complete! Application should be ready.');
            console.log('\n📋 Next steps:');
            console.log('1. Make sure Vite dev server is running: yarn dev:renderer');
            console.log('2. Start Electron app: yarn dev:electron');
            console.log('3. Follow the TEST_GUIDE.md for testing instructions');
        } else {
            console.log('\n⚠️  Some issues detected. Check the errors above.');
        }
    });
}

checkServers(); 