#!/usr/bin/env node

/**
 * Simple script to test backend connectivity
 * Run with: node test-connection.js
 * Or add to package.json scripts: "test:connection": "node test-connection.js"
 */

import axios from 'axios';

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE_URL}/api/v1`;

const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

async function testEndpoint(name, method, url) {
  try {
    const response = await axios({ method, url, timeout: 5000 });
    console.log(`${colors.green}✓${colors.reset} ${name}: ${colors.green}SUCCESS${colors.reset}`);
    console.log(`  Status: ${response.status}`);
    console.log(`  Data:`, JSON.stringify(response.data, null, 2).substring(0, 200));
    return true;
  } catch (error) {
    console.log(`${colors.red}✗${colors.reset} ${name}: ${colors.red}FAILED${colors.reset}`);
    if (error.response) {
      console.log(`  Status: ${error.response.status}`);
      console.log(`  Error: ${error.response.data?.detail || error.message}`);
    } else if (error.request) {
      console.log(`  Error: No response from server (is backend running?)`);
    } else {
      console.log(`  Error: ${error.message}`);
    }
    return false;
  }
}

async function runTests() {
  console.log(`\n${colors.blue}Testing Backend Connection${colors.reset}`);
  console.log(`${colors.yellow}API Base URL: ${API_BASE_URL}${colors.reset}\n`);

  const results = [];

  // Test 1: Health endpoint
  console.log('1. Testing Health Endpoint...');
  results.push(await testEndpoint('Health Check', 'GET', `${API_BASE_URL}/health`));
  console.log('');

  // Test 2: Query health
  console.log('2. Testing Query Service...');
  results.push(await testEndpoint('Query Health', 'GET', `${API_V1}/query/health`));
  console.log('');

  // Test 3: Vector store stats
  console.log('3. Testing Vector Store...');
  results.push(await testEndpoint('Vector Stats', 'GET', `${API_V1}/vector/stats`));
  console.log('');

  // Summary
  const passed = results.filter(r => r).length;
  const total = results.length;

  console.log(`\n${colors.blue}Summary:${colors.reset}`);
  console.log(`  Passed: ${passed}/${total}`);

  if (passed === total) {
    console.log(`\n${colors.green}✓ All tests passed! Backend is connected and ready.${colors.reset}\n`);
    process.exit(0);
  } else {
    console.log(`\n${colors.yellow}⚠ Some tests failed. Check the errors above.${colors.reset}`);
    console.log(`\n${colors.yellow}Make sure the backend is running:${colors.reset}`);
    console.log(`  cd backend`);
    console.log(`  python -m uvicorn app.main:app --reload --port 8000\n`);
    process.exit(1);
  }
}

console.log('\n');
runTests().catch(err => {
  console.error(`${colors.red}Unexpected error:${colors.reset}`, err.message);
  process.exit(1);
});
