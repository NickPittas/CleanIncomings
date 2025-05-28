const fs = require('fs');
const path = require('path');

const requiredIcons = [
  { file: 'icon.ico', platform: 'Windows' },
  { file: 'icon.icns', platform: 'Mac' },
  { file: 'icon.png', platform: 'Linux' },
];

const assetsDir = path.join(__dirname, '..', 'assets');
let missing = [];

for (const icon of requiredIcons) {
  const iconPath = path.join(assetsDir, icon.file);
  if (!fs.existsSync(iconPath)) {
    missing.push(`${icon.file} (${icon.platform})`);
  }
}

if (missing.length > 0) {
  console.error('\x1b[31m[ERROR]\x1b[0m Missing required icon files in assets/:', missing.join(', '));
  console.error('Please add the missing files to the assets directory before packaging.');
  process.exit(1);
} else {
  console.log('[OK] All required icon files are present in assets/.');
} 