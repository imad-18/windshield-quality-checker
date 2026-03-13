import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatMenuModule } from '@angular/material/menu';
import { ThemeService } from './services/theme.service';
import { TranslateService, Lang } from './services/translate.service';
import { TranslatePipe } from './pipes/translate.pipe';

export type TestPhase = 'standby' | 'detecting' | 'measuring' | 'evaluating' | 'complete';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatInputModule, MatSelectModule,
    MatButtonModule, MatProgressBarModule, MatCardModule, MatIconModule,
    MatDividerModule, MatTooltipModule, MatMenuModule, TranslatePipe
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnDestroy {
  // Services
  constructor(public theme: ThemeService, public translate: TranslateService) { }

  // Config
  models = ['VS20', 'VS30', 'VS40'];
  selectedModel = 'VS20';
  tension = 20.0;
  minIntensity = 0.87;
  maxIntensity = 1.26;
  cycleTime = 30; // seconds

  // State
  testPhase: TestPhase = 'standby';
  isTesting = false;
  progress = 0;
  currentIntensity: number | null = null;
  currentResistance: number | null = null;
  testResult: 'PENDING' | 'OK' | 'ERROR' = 'PENDING';
  windshieldId = 0;

  // Readings tracking
  intensityReadings: number[] = [];
  expectedReadings = 0;
  readingsReceived = 0;

  // Sticker
  printSticker: any = null;

  // Languages
  languages: { code: Lang; label: string; flag: string }[] = [
    { code: 'es', label: 'Español', flag: '🇪🇸' },
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
  ];

  private timer: any;
  private phaseTimer: any;

  get currentFlag(): string {
    return this.languages.find(l => l.code === this.translate.currentLang())?.flag ?? '🇪🇸';
  }

  startTest() {
    if (this.isTesting) return;

    this.windshieldId++;
    this.isTesting = true;
    this.progress = 0;
    this.testResult = 'PENDING';
    this.currentIntensity = null;
    this.currentResistance = null;
    this.printSticker = null;
    this.intensityReadings = [];
    this.readingsReceived = 0;

    // Phase 1: Detecting (simulate 1.5s)
    this.testPhase = 'detecting';

    this.phaseTimer = setTimeout(() => {
      // Phase 2: Measuring
      this.testPhase = 'measuring';
      this.startMeasurement();
    }, 1500);
  }

  private startMeasurement() {
    const readingIntervalMs = 200; // read every 200ms
    this.expectedReadings = Math.floor((this.cycleTime * 1000) / readingIntervalMs);
    this.readingsReceived = 0;

    this.timer = setInterval(() => {
      // Simulate real-time intensity reading from equipment
      const baseIntensity = (this.minIntensity + this.maxIntensity) / 2;
      const jitter = (Math.random() - 0.5) * 0.8; // wider jitter for realism
      const reading = parseFloat((baseIntensity + jitter).toFixed(3));

      this.readingsReceived++;
      this.intensityReadings.push(reading);
      this.currentIntensity = reading;

      // Compute resistance R = V / I (Ohm's law)
      if (reading > 0) {
        this.currentResistance = parseFloat((this.tension / reading).toFixed(2));
      }

      // Progress is based on readings received vs expected
      this.progress = Math.min((this.readingsReceived / this.expectedReadings) * 100, 100);

      if (this.readingsReceived >= this.expectedReadings) {
        this.evaluateResult();
      }
    }, readingIntervalMs);
  }

  private evaluateResult() {
    clearInterval(this.timer);
    this.testPhase = 'evaluating';

    // Compute final intensity as average of last 10 readings for stability
    const lastReadings = this.intensityReadings.slice(-10);
    const avgIntensity = lastReadings.reduce((a, b) => a + b, 0) / lastReadings.length;

    // Add slight bias for demo — 70% chance to be in range
    const finalMock = Math.random() > 0.3
      ? parseFloat((Math.random() * (this.maxIntensity - this.minIntensity) + this.minIntensity).toFixed(3))
      : parseFloat(avgIntensity.toFixed(3));

    this.currentIntensity = finalMock;
    if (finalMock > 0) {
      this.currentResistance = parseFloat((this.tension / finalMock).toFixed(2));
    }
    this.progress = 100;

    // Short delay for evaluating phase visibility
    setTimeout(() => {
      if (this.currentIntensity! >= this.minIntensity && this.currentIntensity! <= this.maxIntensity) {
        this.testResult = 'OK';
        this.generateSticker();
      } else {
        this.testResult = 'ERROR';
      }
      this.testPhase = 'complete';
      this.isTesting = false;
    }, 800);
  }

  private generateSticker() {
    const now = new Date();
    this.printSticker = {
      id: this.windshieldId,
      model: this.selectedModel,
      intensity: this.currentIntensity,
      resistance: this.currentResistance,
      tension: this.tension,
      date: now.toLocaleDateString(),
      time: now.toLocaleTimeString(),
      status: 'APPROVED'
    };
  }

  resetTest() {
    this.testPhase = 'standby';
    this.testResult = 'PENDING';
    this.progress = 0;
    this.currentIntensity = null;
    this.currentResistance = null;
    this.printSticker = null;
    this.intensityReadings = [];
    this.readingsReceived = 0;
  }

  setLanguage(lang: Lang) {
    this.translate.setLang(lang);
  }

  ngOnDestroy() {
    if (this.timer) clearInterval(this.timer);
    if (this.phaseTimer) clearTimeout(this.phaseTimer);
  }
}
