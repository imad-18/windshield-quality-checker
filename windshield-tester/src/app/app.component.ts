import { Component, OnDestroy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslatePipe } from './pipes/translate.pipe';
import { TranslateService, Lang } from './services/translate.service';
import { ThemeService } from './services/theme.service';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, TranslatePipe, CommonModule, MatButtonModule, MatMenuModule, MatIconModule, MatTooltipModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent{
  windshieldId = 0;
  selectedModel = 'Model';

  // Services
  constructor(public theme: ThemeService, public translate: TranslateService) { }

  // Languages
  languages: { code: Lang; label: string; flag: string }[] = [
    { code: 'es', label: 'Español', flag: '🇪🇸' },
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
  ];

  get currentFlag(): string {
    return this.languages.find(l => l.code === this.translate.currentLang())?.flag ?? '🇪🇸';
  }

  setLanguage(lang: Lang) {
    this.translate.setLang(lang);
  }
}
