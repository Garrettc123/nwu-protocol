#!/usr/bin/env node

/**
 * Automated Release Notes Generator
 *
 * This script generates structured release notes from git commit history
 * using conventional commit format parsing.
 *
 * Conventional Commit Format:
 * <type>(<scope>): <subject>
 *
 * Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
 * Breaking changes: BREAKING CHANGE: in commit body or ! after type
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Conventional commit type mapping
const TYPE_LABELS = {
  feat: { label: 'Features', emoji: '✨' },
  fix: { label: 'Bug Fixes', emoji: '🐛' },
  docs: { label: 'Documentation', emoji: '📚' },
  style: { label: 'Styles', emoji: '💎' },
  refactor: { label: 'Code Refactoring', emoji: '♻️' },
  perf: { label: 'Performance Improvements', emoji: '⚡' },
  test: { label: 'Tests', emoji: '✅' },
  build: { label: 'Build System', emoji: '🔨' },
  ci: { label: 'Continuous Integration', emoji: '👷' },
  chore: { label: 'Chores', emoji: '🔧' },
  revert: { label: 'Reverts', emoji: '⏪' },
  security: { label: 'Security', emoji: '🔒' },
  breaking: { label: 'BREAKING CHANGES', emoji: '💥' }
};

function executeCommand(command) {
  try {
    return execSync(command, { encoding: 'utf-8' }).trim();
  } catch (error) {
    return '';
  }
}

function getLatestTag() {
  const tag = executeCommand('git describe --tags --abbrev=0 2>/dev/null');
  return tag || '';
}

function getCommitsSinceTag(tag) {
  const command = tag
    ? `git log ${tag}..HEAD --pretty=format:'%H|||%s|||%an|||%ae|||%aI'`
    : `git log --pretty=format:'%H|||%s|||%an|||%ae|||%aI'`;

  const output = executeCommand(command);
  if (!output) return [];

  return output.split('\n').filter(line => line.trim()).map(line => {
    const parts = line.split('|||');
    if (parts.length < 5) return null;

    const [hash, subject, author, email, date] = parts;
    return {
      hash: hash || '',
      subject: subject || '',
      body: '',
      author: author || '',
      email: email || '',
      date: date || ''
    };
  }).filter(Boolean);
}

function parseConventionalCommit(commit) {
  const conventionalPattern = /^(\w+)(\(([^)]+)\))?(!)?:\s*(.+)$/;
  const match = commit.subject.match(conventionalPattern);

  if (!match) {
    // Non-conventional commit
    return {
      type: 'other',
      scope: null,
      breaking: false,
      subject: commit.subject,
      body: commit.body,
      hash: commit.hash,
      author: commit.author,
      email: commit.email,
      date: commit.date
    };
  }

  const [, type, , scope, breaking, subject] = match;
  const hasBreakingInBody = commit.body && commit.body.includes('BREAKING CHANGE');

  return {
    type,
    scope: scope || null,
    breaking: breaking === '!' || hasBreakingInBody,
    subject,
    body: commit.body,
    hash: commit.hash,
    author: commit.author,
    email: commit.email,
    date: commit.date
  };
}

function categorizeCommits(commits) {
  const categories = {
    breaking: [],
    feat: [],
    fix: [],
    docs: [],
    style: [],
    refactor: [],
    perf: [],
    test: [],
    build: [],
    ci: [],
    chore: [],
    revert: [],
    security: [],
    other: []
  };

  commits.forEach(commit => {
    const parsed = parseConventionalCommit(commit);

    if (parsed.breaking) {
      categories.breaking.push(parsed);
    }

    if (categories[parsed.type]) {
      categories[parsed.type].push(parsed);
    } else {
      categories.other.push(parsed);
    }
  });

  return categories;
}

function generateMarkdownSection(type, commits) {
  if (commits.length === 0) return '';

  const config = TYPE_LABELS[type];
  if (!config) return '';

  let section = `### ${config.emoji} ${config.label}\n\n`;

  commits.forEach(commit => {
    const scope = commit.scope ? `**${commit.scope}**: ` : '';
    const shortHash = commit.hash.substring(0, 7);
    section += `- ${scope}${commit.subject} ([${shortHash}](https://github.com/Garrettc123/nwu-protocol/commit/${commit.hash}))\n`;
  });

  section += '\n';
  return section;
}

function generateReleaseNotes(version, tag) {
  const commits = getCommitsSinceTag(tag);

  if (commits.length === 0) {
    return 'No changes since last release.';
  }

  const categories = categorizeCommits(commits);
  const date = new Date().toISOString().split('T')[0];

  let notes = `# Release ${version}\n\n`;
  notes += `**Release Date:** ${date}\n\n`;
  notes += `**Commits:** ${commits.length}\n\n`;

  // Generate sections in priority order
  const sectionOrder = [
    'breaking',
    'feat',
    'fix',
    'security',
    'perf',
    'refactor',
    'docs',
    'test',
    'build',
    'ci',
    'chore',
    'style',
    'revert'
  ];

  sectionOrder.forEach(type => {
    if (categories[type].length > 0) {
      notes += generateMarkdownSection(type, categories[type]);
    }
  });

  // Add other commits if any
  if (categories.other.length > 0) {
    notes += '### 📝 Other Changes\n\n';
    categories.other.forEach(commit => {
      const shortHash = commit.hash.substring(0, 7);
      notes += `- ${commit.subject} ([${shortHash}](https://github.com/Garrettc123/nwu-protocol/commit/${commit.hash}))\n`;
    });
    notes += '\n';
  }

  // Add contributors section
  const contributors = [...new Set(commits.map(c => c.author))];
  if (contributors.length > 0) {
    notes += '### 👥 Contributors\n\n';
    contributors.forEach(contributor => {
      notes += `- ${contributor}\n`;
    });
    notes += '\n';
  }

  return notes;
}

function updateChangelog(version, releaseNotes) {
  const changelogPath = path.join(process.cwd(), 'CHANGELOG.md');

  if (!fs.existsSync(changelogPath)) {
    console.error('CHANGELOG.md not found. Creating new file...');
    fs.writeFileSync(changelogPath, '# Changelog\n\n');
  }

  const changelog = fs.readFileSync(changelogPath, 'utf-8');
  const date = new Date().toISOString().split('T')[0];

  // Find the position to insert the new release
  const unreleasedMatch = changelog.match(/## \[Unreleased\]/);

  if (!unreleasedMatch) {
    console.error('Could not find [Unreleased] section in CHANGELOG.md');
    return;
  }

  const insertPosition = unreleasedMatch.index + unreleasedMatch[0].length;

  const newEntry = `\n\n## [${version}] - ${date}\n\n${releaseNotes}\n`;

  const updatedChangelog =
    changelog.slice(0, insertPosition) +
    newEntry +
    changelog.slice(insertPosition);

  fs.writeFileSync(changelogPath, updatedChangelog);
  console.log(`✅ CHANGELOG.md updated with version ${version}`);
}

function generateCompactChangelog(tag) {
  const commits = getCommitsSinceTag(tag);

  if (commits.length === 0) {
    return 'No changes';
  }

  const categories = categorizeCommits(commits);
  let compact = '';

  // Breaking changes first
  if (categories.breaking.length > 0) {
    compact += '💥 BREAKING CHANGES:\n';
    categories.breaking.forEach(c => {
      compact += `  - ${c.subject}\n`;
    });
  }

  // Features
  if (categories.feat.length > 0) {
    compact += '✨ Features:\n';
    categories.feat.slice(0, 5).forEach(c => {
      compact += `  - ${c.subject}\n`;
    });
    if (categories.feat.length > 5) {
      compact += `  ... and ${categories.feat.length - 5} more\n`;
    }
  }

  // Fixes
  if (categories.fix.length > 0) {
    compact += '🐛 Fixes:\n';
    categories.fix.slice(0, 5).forEach(c => {
      compact += `  - ${c.subject}\n`;
    });
    if (categories.fix.length > 5) {
      compact += `  ... and ${categories.fix.length - 5} more\n`;
    }
  }

  return compact;
}

// Main execution
const args = process.argv.slice(2);
const command = args[0] || 'generate';
const version = args[1] || 'unreleased';

switch (command) {
  case 'generate':
    const tag = getLatestTag();
    const notes = generateReleaseNotes(version, tag);
    console.log(notes);
    break;

  case 'update':
    const currentTag = getLatestTag();
    const releaseNotes = generateReleaseNotes(version, currentTag);
    updateChangelog(version, releaseNotes);
    break;

  case 'compact':
    const latestTag = getLatestTag();
    const compact = generateCompactChangelog(latestTag);
    console.log(compact);
    break;

  default:
    console.log('Usage:');
    console.log('  node generate-release-notes.js generate [version]  - Generate release notes');
    console.log('  node generate-release-notes.js update [version]    - Update CHANGELOG.md');
    console.log('  node generate-release-notes.js compact             - Generate compact changelog');
    process.exit(1);
}
