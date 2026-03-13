import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
    isDark = signal(false);

    constructor() {
        const saved = localStorage.getItem('wt-theme');
        if (saved) {
            this.isDark.set(saved === 'dark');
        } else {
            this.isDark.set(window.matchMedia('(prefers-color-scheme: dark)').matches);
        }
        this.applyTheme();
    }

    toggle() {
        this.isDark.set(!this.isDark());
        this.applyTheme();
    }

    private applyTheme() {
        const theme = this.isDark() ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('wt-theme', theme);
    }
}
