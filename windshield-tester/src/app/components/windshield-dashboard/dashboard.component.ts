import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService } from './dashboard.service';

interface TestRecord {
    id: number;
    tension: number;
    final_intensity: number;
    final_resistance: number;
    result: string;
    created_at: string;
}

interface PaginationInfo {
    limit: number;
    offset: number;
    total: number;
    pages: number;
}

interface StatsData {
    total_tests: number;
    ok_count: number;
    error_count: number;
    ok_percentage: number;
    avg_intensity: number;
    last_test: string | null;
}

@Component({
    selector: 'app-windshield-dashboard',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.css'],
})
export class WindshieldDashboardComponent implements OnInit {
    // Data
    tests: TestRecord[] = [];
    stats: StatsData | null = null;

    // Pagination
    pagination: PaginationInfo = {
        limit: 10,
        offset: 0,
        total: 0,
        pages: 0,
    };

    // Filters
    filters = {
        result: '',
        start_date: '',
        end_date: '',
        search_id: '',
    };

    // UI State
    isLoading = false;
    isExporting = false;
    errorMessage = '';
    successMessage = '';

    constructor(private dashboardService: DashboardService) { }

    ngOnInit(): void {
        this.loadTests();
        this.loadStats();
    }

    /**
     * Load tests from API with current filters
     */
    loadTests(): void {
        this.isLoading = true;
        this.errorMessage = '';

        const params: any = {
            limit: this.pagination.limit,
            offset: this.pagination.offset,
        };

        if (this.filters.result) {
            params.result = this.filters.result;
        }
        if (this.filters.start_date) {
            params.start_date = this.filters.start_date;
        }
        if (this.filters.end_date) {
            params.end_date = this.filters.end_date;
        }

        this.dashboardService.getTests(params).subscribe({
            next: (response: any) => {
                this.tests = response.data;
                this.pagination = response.pagination;

                // If searching by ID and only one result, show it
                if (
                    this.filters.search_id &&
                    this.tests.length === 1 &&
                    this.tests[0].id === parseInt(this.filters.search_id)
                ) {
                    this.successMessage = `Found test #${this.filters.search_id}`;
                } else if (this.tests.length === 0) {
                    this.errorMessage = 'No test records found matching your filters';
                }

                this.isLoading = false;
            },
            error: (error) => {
                console.error('Error loading tests:', error);
                this.errorMessage =
                    error.error?.detail || 'Failed to load test data. Please try again.';
                this.isLoading = false;
            },
        });
    }

    /**
     * Load dashboard statistics
     */
    loadStats(): void {
        this.dashboardService.getStats().subscribe({
            next: (response: any) => {
                this.stats = response.data;
            },
            error: (error) => {
                console.error('Error loading stats:', error);
            },
        });
    }

    /**
     * Apply filters and reload data
     */
    applyFilters(): void {
        this.pagination.offset = 0; // Reset to first page
        this.loadTests();
    }

    /**
     * Clear all filters
     */
    clearFilters(): void {
        this.filters = {
            result: '',
            start_date: '',
            end_date: '',
            search_id: '',
        };
        this.pagination.offset = 0;
        this.errorMessage = '';
        this.successMessage = '';
        this.loadTests();
    }

    /**
     * Refresh data (reload current page)
     */
    refreshData(): void {
        this.successMessage = '';
        this.errorMessage = '';
        this.loadTests();
        this.loadStats();
    }

    /**
     * Go to previous page
     */
    previousPage(): void {
        if (this.pagination.offset > 0) {
            this.pagination.offset -= this.pagination.limit;
            this.loadTests();
        }
    }

    /**
     * Go to next page
     */
    nextPage(): void {
        if (
            this.pagination.offset + this.pagination.limit <
            this.pagination.total
        ) {
            this.pagination.offset += this.pagination.limit;
            this.loadTests();
        }
    }

    /**
     * Jump to specific page
     */
    goToPage(pageNumber: number): void {
        this.pagination.offset = (pageNumber - 1) * this.pagination.limit;
        this.loadTests();
    }

    /**
     * Export filtered data as CSV
     */
    exportAsCSV(): void {
        this.isExporting = true;
        this.errorMessage = '';

        const params: any = {};

        if (this.filters.result) {
            params.result = this.filters.result;
        }
        if (this.filters.start_date) {
            params.start_date = this.filters.start_date;
        }
        if (this.filters.end_date) {
            params.end_date = this.filters.end_date;
        }

        this.dashboardService.exportCSV(params).subscribe({
            next: (response: any) => {
                // Create blob and download
                const blob = new Blob([response.content], {
                    type: 'text/csv;charset=utf-8;',
                });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);

                link.setAttribute('href', url);
                link.setAttribute('download', response.filename);
                link.style.visibility = 'hidden';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                this.successMessage = `Downloaded ${response.filename}`;
                this.isExporting = false;

                // Clear success message after 3 seconds
                setTimeout(() => {
                    this.successMessage = '';
                }, 3000);
            },
            error: (error) => {
                console.error('Error exporting CSV:', error);
                this.errorMessage = 'Failed to export data. Please try again.';
                this.isExporting = false;
            },
        });
    }

    /**
     * Format date for display
     */
    formatDate(dateString: string): string {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
            });
        } catch {
            return dateString;
        }
    }

    /**
     * Format number to 3 decimal places
     */
    formatNumber(value: number): string {
        if (!value) return '0';
        return parseFloat(value.toString()).toFixed(3);
    }

    /**
     * Get CSS class for result badge
     */
    getResultClass(result: string): string {
        return result === 'OK' ? 'badge-ok' : 'badge-error';
    }

    /**
     * Get current page number
     */
    getCurrentPage(): number {
        return (
            Math.floor(this.pagination.offset / this.pagination.limit) + 1
        );
    }

    /**
     * Get array of page numbers for pagination buttons
     */
    getPageNumbers(): number[] {
        const pages = [];
        const maxPages = Math.min(this.pagination.pages, 5); // Show max 5 page buttons

        let startPage = Math.max(
            1,
            this.getCurrentPage() - Math.floor(maxPages / 2)
        );
        let endPage = Math.min(
            this.pagination.pages,
            startPage + maxPages - 1
        );

        if (endPage - startPage + 1 < maxPages) {
            startPage = Math.max(1, endPage - maxPages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        return pages;
    }

    /**
     * Check if can go to previous page
     */
    canPreviousPage(): boolean {
        return this.pagination.offset > 0;
    }

    /**
     * Check if can go to next page
     */
    canNextPage(): boolean {
        return (
            this.pagination.offset + this.pagination.limit <
            this.pagination.total
        );
    }
}
