/**
 * Unit tests for Vercel deployment configuration.
 *
 * These tests validate that vercel.json exists and contains
 * required fields for production deployment.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'fs';
import path from 'path';

describe('Vercel Configuration', () => {
  const vercelJsonPath = path.join(process.cwd(), 'vercel.json');

  describe('File Existence', () => {
    it('should have vercel.json file', () => {
      expect(existsSync(vercelJsonPath)).toBe(true);
    });
  });

  describe('Basic Configuration', () => {
    it('should have valid JSON structure', () => {
      const content = readFileSync(vercelJsonPath, 'utf-8');
      expect(() => JSON.parse(content)).not.toThrow();
    });

    it('should have correct version', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.version).toBe(2);
    });

    it('should have correct framework', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.framework).toBe('vite');
    });
  });

  describe('Build Configuration', () => {
    it('should have buildCommand', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.buildCommand).toBeDefined();
      expect(vercelJson.buildCommand).toBe('npm run build');
    });

    it('should have outputDirectory', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.outputDirectory).toBeDefined();
      expect(vercelJson.outputDirectory).toBe('dist');
    });

    it('should have installCommand', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.installCommand).toBeDefined();
      expect(vercelJson.installCommand).toBe('npm install');
    });
  });

  describe('Environment Variables', () => {
    it('should have VITE_API_BASE_URL configured', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.env).toBeDefined();
      expect(vercelJson.env.VITE_API_BASE_URL).toBeDefined();
      expect(vercelJson.env.VITE_API_BASE_URL.value).toContain('https://');
    });

    it('should have VITE_WS_BASE_URL configured', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.env).toBeDefined();
      expect(vercelJson.env.VITE_WS_BASE_URL).toBeDefined();
      expect(vercelJson.env.VITE_WS_BASE_URL.value).toContain('wss://');
    });

    it('should have development values for local testing', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      const apiUrl = vercelJson.env.VITE_API_BASE_URL;

      expect(apiUrl.development).toBeDefined();
      expect(apiUrl.development.value).toContain('http://localhost');
    });
  });

  describe('Security Headers', () => {
    it('should have security headers configured', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.headers).toBeDefined();
      expect(vercelJson.headers.length).toBeGreaterThan(0);
    });

    it('should have X-Content-Type-Options header', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      const headers = vercelJson.headers[0].headers;

      const contentTypeHeader = headers.find(
        (h: any) => h.key === 'X-Content-Type-Options'
      );
      expect(contentTypeHeader).toBeDefined();
      expect(contentTypeHeader.value).toBe('nosniff');
    });

    it('should have X-Frame-Options header', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      const headers = vercelJson.headers[0].headers;

      const frameOptionsHeader = headers.find(
        (h: any) => h.key === 'X-Frame-Options'
      );
      expect(frameOptionsHeader).toBeDefined();
      expect(frameOptionsHeader.value).toBe('DENY');
    });

    it('should have X-XSS-Protection header', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      const headers = vercelJson.headers[0].headers;

      const xssHeader = headers.find(
        (h: any) => h.key === 'X-XSS-Protection'
      );
      expect(xssHeader).toBeDefined();
      expect(xssHeader.value).toContain('mode=block');
    });
  });

  describe('SPA Routing', () => {
    it('should have rewrites for SPA routing', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      expect(vercelJson.rewrites).toBeDefined();
      expect(vercelJson.rewrites.length).toBeGreaterThan(0);
    });

    it('should rewrite all routes to index.html', () => {
      const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
      const rewrite = vercelJson.rewrites[0];

      expect(rewrite.source).toBe('/(.*)');
      expect(rewrite.destination).toBe('/index.html');
    });
  });
});
