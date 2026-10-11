import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests/browser',timeout:30000,use:{baseURL:process.env.CPU_LAB_BASE_URL??'http://127.0.0.1:5196',viewport:{width:1600,height:1000},launchOptions:{args:process.platform==='darwin'?['--use-angle=metal','--enable-gpu','--ignore-gpu-blocklist']:[]}},reporter:'list',outputDir:'/tmp/cpu-lab-playwright'});
