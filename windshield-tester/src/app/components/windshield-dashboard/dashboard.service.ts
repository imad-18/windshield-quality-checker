import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

/**
 * Dashboard Service
 * Provides HTTP methods to communicate with the FastAPI backend dashboard endpoints
 */
@Injectable({
    providedIn: 'root',
})
export class DashboardService {
    private baseUrl = 'http://localhost:8000/api/dashboard';  // Use localhost for local development

    // Fallback for local development
    private localUrl = 'http://localhost:8000/api/dashboard';

    constructor(private http: HttpClient) { }

    /**
     * Get the API URL (tries production URL first, falls back to localhost)
     */
    private getApiUrl(): string {
        // In a real application, use environment configuration
        // For now, we'll try the Docker service name first
        return this.baseUrl;
    }

    /**
     * Get all tests with optional filters and pagination
     *
     * @param filters Object containing filter parameters:
     *   - limit: number of records (default 10)
     *   - offset: number of records to skip (default 0)
     *   - result: 'OK' or 'ERROR' (optional)
     *   - start_date: 'YYYY-MM-DD' (optional)
     *   - end_date: 'YYYY-MM-DD' (optional)
     *
     * @returns Observable<ApiResponse> with test data and pagination info
     *
     * Example:
     * this.dashboardService.getTests({
     *   limit: 20,
     *   offset: 0,
     *   result: 'OK',
     *   start_date: '2026-05-01',
     *   end_date: '2026-05-18'
     * })
     */
    getTests(filters: any = {}): Observable<any> {
        let params = new HttpParams();

        // Add filter parameters
        if (filters.limit) {
            params = params.set('limit', filters.limit.toString());
        }
        if (filters.offset !== undefined && filters.offset !== null) {
            params = params.set('offset', filters.offset.toString());
        }
        if (filters.result) {
            params = params.set('result', filters.result);
        }
        if (filters.start_date) {
            params = params.set('start_date', filters.start_date);
        }
        if (filters.end_date) {
            params = params.set('end_date', filters.end_date);
        }

        return this.http.get<any>(`${this.getApiUrl()}/tests`, { params });
    }

    /**
     * Get a single test by ID
     *
     * @param testId The ID of the test to retrieve
     * @returns Observable<ApiResponse> with single test data
     *
     * Example:
     * this.dashboardService.getTestById(42)
     */
    getTestById(testId: number): Observable<any> {
        return this.http.get<any>(`${this.getApiUrl()}/tests/${testId}`);
    }

    /**
     * Export tests as CSV with optional filters
     *
     * @param filters Object containing filter parameters (same as getTests):
     *   - result: 'OK' or 'ERROR' (optional)
     *   - start_date: 'YYYY-MM-DD' (optional)
     *   - end_date: 'YYYY-MM-DD' (optional)
     *
     * @returns Observable<ApiResponse> with CSV content and filename
     *
     * Example:
     * this.dashboardService.exportCSV({
     *   result: 'OK',
     *   start_date: '2026-05-01'
     * })
     */
    exportCSV(filters: any = {}): Observable<any> {
        let params = new HttpParams();

        if (filters.result) {
            params = params.set('result', filters.result);
        }
        if (filters.start_date) {
            params = params.set('start_date', filters.start_date);
        }
        if (filters.end_date) {
            params = params.set('end_date', filters.end_date);
        }

        return this.http.get<any>(`${this.getApiUrl()}/export`, { params });
    }

    /**
     * Get dashboard statistics
     *
     * @returns Observable<StatsResponse> with aggregated statistics
     * Returns:
     *   - total_tests: Total number of tests
     *   - ok_count: Number of OK tests
     *   - error_count: Number of ERROR tests
     *   - ok_percentage: Percentage of OK tests (0-100)
     *   - avg_intensity: Average final_intensity value
     *   - last_test: ISO timestamp of most recent test
     *
     * Example:
     * this.dashboardService.getStats()
     */
    getStats(): Observable<any> {
        return this.http.get<any>(`${this.getApiUrl()}/stats`);
    }

    /**
     * Health check to verify backend connectivity
     *
     * @returns Observable<any> - simple health check response
     *
     * Example:
     * this.dashboardService.healthCheck()
     */
    healthCheck(): Observable<any> {
        return this.http.get<any>(`${this.getApiUrl()}/health`);
    }
}
