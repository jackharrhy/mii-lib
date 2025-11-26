#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');

// Supported Mii data formats from script.js
const supportedTypes = [
  {
    name: 'FFLiMiiDataCore',
    sizes: [72],
    offsetName: 0x1A,
  },
  {
    name: 'FFLiMiiDataOfficial',
    sizes: [92],
    offsetName: 0x1A,
  },
  {
    name: 'FFLStoreData',
    sizes: [96],
    offsetCRC16: 94,
    offsetName: 0x1A,
  },
  {
    name: 'FFLStoreData',
    sizes: [104, 106, 108, 336],
    offsetCRC16: 94,
    offsetName: 0x1A,
    specialCaseConvertTo: true
  },
  {
    name: 'RFLCharData',
    sizes: [74],
    offsetName: 0x2,
    isNameU16BE: true
  },
  {
    name: 'RFLStoreData',
    sizes: [76],
    offsetCRC16: 74,
    offsetName: 0x2,
    isNameU16BE: true
  },
  {
    name: 'nn::mii::CharInfo',
    sizes: [88],
    offsetName: 0x10,
  },
  {
    name: 'nn::mii::CoreData',
    sizes: [48, 68],
    offsetName: 0x1C,
  },
  {
    name: 'Mii Studio Data',
    sizes: [46, 47],
  },
];

// Nintendo's official clothes/favorite colors (the primary Mii color used by games)
const CLOTHES_COLORS = [
  '#FF0000', // 0 - red
  '#FF8000', // 1 - orange
  '#FFFF00', // 2 - yellow  
  '#80FF00', // 3 - light green
  '#00FF00', // 4 - dark green
  '#0000FF', // 5 - blue
  '#00FFFF', // 6 - light blue
  '#FF00FF', // 7 - pink
  '#8000FF', // 8 - purple
  '#8B4513', // 9 - brown
  '#FFFFFF', // 10 - white
  '#000000'  // 11 - black
];

function findSupportedTypeBySize(size) {
  return supportedTypes.find(type => type.sizes.includes(size));
}

function crc16(data) {
  let crc = 0;
  let msb = crc >> 8;
  let lsb = crc & 0xFF;

  for (let i = 0; i < data.length; i++) {
    let c = data[i];
    let x = c ^ msb;
    x ^= (x >> 4);
    msb = (lsb ^ (x >> 3) ^ (x << 4)) & 0xFF;
    lsb = (x ^ (x << 5)) & 0xFF;
  }

  crc = (msb << 8) + lsb;
  return crc;
}

function extractUTF16Text(data, startOffset, isBigEndian, nameLength = 10) {
  const length = nameLength * 2;
  let endPosition = startOffset;

  while (endPosition < startOffset + length) {
    if (data[endPosition] === 0x00 && data[endPosition + 1] === 0x00) {
      break;
    }
    endPosition += 2;
  }

  const nameBytes = data.slice(startOffset, endPosition);
  
  if (isBigEndian) {
    // Convert UTF-16BE to UTF-16LE for Node.js
    for (let i = 0; i < nameBytes.length; i += 2) {
      const temp = nameBytes[i];
      nameBytes[i] = nameBytes[i + 1];
      nameBytes[i + 1] = temp;
    }
  }
  
  return nameBytes.toString('utf16le');
}

function getMiiName(data, type) {
  if (!type || !type.offsetName) {
    return type ? type.name : 'Unknown';
  }

  return extractUTF16Text(data, type.offsetName, type.isNameU16BE);
}

function extractMiiClothesColor(data, type) {
  if (!type) {
    return 'Unknown';
  }

  try {
    let clothesColorIndex;

    if (type.name === 'FFLStoreData' && data.length === 96) {
      // 3DS/Wii U format: Offset 0x18, bits 10-13 (little endian)
      const byte1 = data[0x18];
      const byte2 = data[0x19];
      const combined = (byte2 << 8) | byte1; // Little endian
      clothesColorIndex = (combined >> 10) & 0x0F; // Extract bits 10-13
      
    } else if (type.name === 'RFLCharData' && data.length === 74) {
      // Original Wii format: Offset 0x00-0x01, bits 5-8 (big endian)
      const byte1 = data[0x00];
      const byte2 = data[0x01];
      const combined = (byte1 << 8) | byte2; // Big endian
      clothesColorIndex = (combined >> 8) & 0x0F; // Extract bits 5-8 (bits 8-11 when counting from MSB)
      
    } else if (type.name === 'RFLStoreData' && data.length === 76) {
      // Wii format with CRC: Same as RFLCharData for the color data
      const byte1 = data[0x00];
      const byte2 = data[0x01];
      const combined = (byte1 << 8) | byte2; // Big endian
      clothesColorIndex = (combined >> 8) & 0x0F; // Extract bits 5-8
      
    } else {
      // Unsupported format for color extraction
      return 'Unknown';
    }
    
    return CLOTHES_COLORS[clothesColorIndex] || 'Unknown';
  } catch (error) {
    return 'Error';
  }
}

function validateMiiData(data, type) {
  if (!type) {
    return { valid: false, error: `Unsupported file size: ${data.length} bytes` };
  }

  if (type.offsetCRC16) {
    const dataCrc16 = data.slice(type.offsetCRC16, type.offsetCRC16 + 2);
    const dataCrc16u16 = (dataCrc16[0] << 8) | dataCrc16[1];
    const expectedCrc16 = crc16(data.slice(0, type.offsetCRC16));

    if (expectedCrc16 !== dataCrc16u16) {
      return { valid: false, error: 'Invalid CRC16 checksum' };
    }
  }

  return { valid: true };
}

function sanitizeFileName(name) {
  // Replace invalid filename characters with underscores
  return name.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').trim();
}

async function downloadImage(url, fileName) {
  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        return;
      }

      const fileStream = fs.createWriteStream(fileName);
      response.pipe(fileStream);

      fileStream.on('finish', () => {
        fileStream.close();
        resolve(fileName);
      });

      fileStream.on('error', (err) => {
        fs.unlink(fileName, () => {}); // Delete partial file
        reject(err);
      });
    }).on('error', reject);
  });
}

async function processMiiFile(filePath, shouldDownload = false) {
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found: ${filePath}`);
    return;
  }

  const data = fs.readFileSync(filePath);
  const type = findSupportedTypeBySize(data.length);
  
  const validation = validateMiiData(data, type);
  if (!validation.valid) {
    console.error(`Error: ${validation.error}`);
    return;
  }

  const miiName = getMiiName(data, type);
  const base64Data = data.toString('base64');
  
  // URL encode base64 data for use in URLs
  const urlEncodedData = encodeURIComponent(base64Data);
  const imageUrl = `https://mii-unsecure.ariankordi.net/miis/image.png?data=${urlEncodedData}&type=face&width=270&characterYRotate=15`;
  
  console.log(`File: ${filePath}`);
  console.log(`Mii Name: ${miiName}`);
  console.log(`Format: ${type.name} (${data.length} bytes)`);
  console.log(`Base64: ${base64Data}`);
  console.log(`URL: ${imageUrl}`);

  if (shouldDownload) {
    try {
      const sanitizedName = sanitizeFileName(miiName || 'Unknown');
      const outputFileName = `${sanitizedName}.png`;
      console.log(`Downloading to: ${outputFileName}`);
      
      await downloadImage(imageUrl, outputFileName);
      console.log(`✓ Downloaded: ${outputFileName}`);
    } catch (error) {
      console.error(`✗ Download failed: ${error.message}`);
    }
  }

  console.log('---');

  return {
    fileName: path.basename(filePath, path.extname(filePath)),
    miiName,
    base64Data,
    urlEncodedData,
    format: type.name,
    size: data.length,
    imageUrl
  };
}

async function exportMiisToCsv(filePaths, outputFile = 'miis.csv') {
  const results = [];
  
  console.log('Processing Mii files for CSV export...');
  
  for (const filePath of filePaths) {
    if (!fs.existsSync(filePath)) {
      console.error(`Error: File not found: ${filePath}`);
      continue;
    }

    const data = fs.readFileSync(filePath);
    const type = findSupportedTypeBySize(data.length);
    
    const validation = validateMiiData(data, type);
    if (!validation.valid) {
      console.error(`Error processing ${filePath}: ${validation.error}`);
      continue;
    }

    const miiName = getMiiName(data, type);
    const clothesColor = extractMiiClothesColor(data, type);
    
    results.push({
      fileName: path.basename(filePath, path.extname(filePath)),
      name: miiName || 'Unknown',
      clothesColor: clothesColor,
      format: type.name,
      size: data.length
    });
    
    process.stdout.write('.');
  }
  
  console.log(`\n\nGenerating CSV with ${results.length} Miis...`);
  
  // Create CSV content
  const csvHeader = 'filename,name,clothes_color,format,size_bytes\n';
  const csvRows = results.map(result => 
    `"${result.fileName}","${result.name}","${result.clothesColor}","${result.format}",${result.size}`
  ).join('\n');
  
  const csvContent = csvHeader + csvRows;
  
  fs.writeFileSync(outputFile, csvContent);
  console.log(`✓ CSV exported to: ${outputFile}`);
  
  return results;
}

function showUsage() {
  console.log('Mii CLI - Process .mii files and extract information');
  console.log('');
  console.log('Usage:');
  console.log('  node mii-to-base64.js convert [--download] <mii-file> [mii-file2] ...');
  console.log('  node mii-to-base64.js csv [--output <file>] <mii-file> [mii-file2] ...');
  console.log('');
  console.log('Commands:');
  console.log('  convert    Convert Mii files to base64 and generate URLs');
  console.log('  csv        Export Mii data to CSV file with clothes color');
  console.log('');
  console.log('Options:');
  console.log('  --download       Download rendered images as {mii-name}.png (convert only)');
  console.log('  --output <file>  Specify output CSV filename (csv only, default: miis.csv)');
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    showUsage();
    process.exit(1);
  }
  
  const command = args[0];
  
  if (command === 'convert') {
    const convertArgs = args.slice(1);
    
    // Check for --download flag
    const downloadIndex = convertArgs.indexOf('--download');
    const shouldDownload = downloadIndex !== -1;
    
    // Remove --download from args if present
    if (shouldDownload) {
      convertArgs.splice(downloadIndex, 1);
    }
    
    if (convertArgs.length === 0) {
      console.error('Error: No Mii files specified for conversion');
      showUsage();
      process.exit(1);
    }

    const results = [];
    
    for (const filePath of convertArgs) {
      const result = await processMiiFile(filePath, shouldDownload);
      if (result) {
        results.push(result);
      }
    }

    if (results.length > 1) {
      console.log('\nSUMMARY:');
      results.forEach(result => {
        console.log(`${result.fileName}: ${result.miiName} (${result.format})`);
      });
      
      if (shouldDownload) {
        console.log(`\nDownloaded ${results.length} Mii images as PNG files.`);
      }
    }
    
  } else if (command === 'csv') {
    const csvArgs = args.slice(1);
    
    // Check for --output flag
    const outputIndex = csvArgs.indexOf('--output');
    let outputFile = 'miis.csv';
    
    if (outputIndex !== -1 && outputIndex + 1 < csvArgs.length) {
      outputFile = csvArgs[outputIndex + 1];
      csvArgs.splice(outputIndex, 2); // Remove --output and filename
    }
    
    if (csvArgs.length === 0) {
      console.error('Error: No Mii files specified for CSV export');
      showUsage();
      process.exit(1);
    }
    
    await exportMiisToCsv(csvArgs, outputFile);
    
  } else {
    console.error(`Unknown command: ${command}`);
    showUsage();
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { processMiiFile, getMiiName, validateMiiData };
