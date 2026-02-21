/* eslint-disable @typescript-eslint/no-require-imports */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

try {
    // Get git log with format: hash|date|author|message
    // Limit to last 50 commits to avoid huge file
    const log = execSync('git log --pretty=format:"%h|%ad|%an|%s" --date=short -n 50').toString();

    const commits = log.split('\n').map(line => {
        // Split by | but only for the first 3 occurrences to handle | in message
        const parts = line.split('|');
        if (parts.length < 4) return null;

        const hash = parts[0];
        const date = parts[1];
        const author = parts[2];
        const message = parts.slice(3).join('|'); // Re-join message if it contained |

        return { hash, date, author, message };
    }).filter(Boolean);

    const outputPath = path.join(__dirname, '../public/changelog.json');

    // Ensure directory exists just in case
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(commits, null, 2));
    console.log('✅ Changelog generated at', outputPath);
} catch (error) {
    console.error('⚠️ Failed to generate changelog:', error.message);
    // Write empty array to avoid frontend crash if git fails
    const outputPath = path.join(__dirname, '../public/changelog.json');
    if (!fs.existsSync(outputPath)) {
        fs.writeFileSync(outputPath, '[]');
    }
}
