import { Injectable, signal } from '@angular/core';

export type Lang = 'es' | 'en' | 'fr';

const TRANSLATIONS: Record<Lang, Record<string, string>> = {
    es: {
        'app.title': 'TRAZABILIDAD FUENTE ALIMENTACIÓN',
        'app.subtitle': 'Sistema de control de calidad de parabrisas',
        'config.title': 'Parámetros de Configuración',
        'config.model': 'MODELO',
        'config.tension': 'TENSIÓN (V)',
        'config.intensity': 'INTENSIDAD (A)',
        'config.min': 'MÍN.',
        'config.max': 'MÁX.',
        'config.cycle': 'T. CICLO (S)',
        'action.start': 'INICIAR PRUEBA',
        'action.reset': 'REINICIAR',
        'progress.title': 'PROGRESO DE MEDICIÓN',
        'metrics.intensity': 'INTENSIDAD ACTUAL (A)',
        'metrics.resistance': 'RESISTENCIA (Ω)',
        'result.title': 'RESULTADO',
        'result.ok': 'CONFORME',
        'result.error': 'NO CONFORME',
        'result.pending': 'EN ESPERA',
        'sticker.title': 'ETIQUETA GENERADA',
        'sticker.model': 'MODELO',
        'sticker.intensity': 'INTENSIDAD',
        'sticker.resistance': 'RESISTENCIA',
        'sticker.date': 'FECHA',
        'sticker.time': 'HORA',
        'sticker.status': 'ESTADO',
        'sticker.approved': 'APROBADO',
        'phase.standby': 'EN ESPERA',
        'phase.detecting': 'DETECTANDO PARABRISAS',
        'phase.measuring': 'MIDIENDO INTENSIDAD',
        'phase.evaluating': 'EVALUANDO CONFORMIDAD',
        'phase.complete': 'COMPLETADO',
        'windshield.id': 'PARABRISAS N°',
        'theme.toggle': 'Cambiar tema',
        'readings.count': 'Lecturas',
    },
    en: {
        'app.title': 'POWER SUPPLY TRACEABILITY',
        'app.subtitle': 'Windshield quality control system',
        'config.title': 'Configuration Parameters',
        'config.model': 'MODEL',
        'config.tension': 'TENSION (V)',
        'config.intensity': 'INTENSITY (A)',
        'config.min': 'MIN.',
        'config.max': 'MAX.',
        'config.cycle': 'CYCLE TIME (S)',
        'action.start': 'START TEST',
        'action.reset': 'RESET',
        'progress.title': 'MEASUREMENT PROGRESS',
        'metrics.intensity': 'CURRENT INTENSITY (A)',
        'metrics.resistance': 'RESISTANCE (Ω)',
        'result.title': 'RESULT',
        'result.ok': 'PASS',
        'result.error': 'FAIL',
        'result.pending': 'STANDBY',
        'sticker.title': 'STICKER GENERATED',
        'sticker.model': 'MODEL',
        'sticker.intensity': 'INTENSITY',
        'sticker.resistance': 'RESISTANCE',
        'sticker.date': 'DATE',
        'sticker.time': 'TIME',
        'sticker.status': 'STATUS',
        'sticker.approved': 'APPROVED',
        'phase.standby': 'STANDBY',
        'phase.detecting': 'DETECTING WINDSHIELD',
        'phase.measuring': 'MEASURING INTENSITY',
        'phase.evaluating': 'EVALUATING CONFORMITY',
        'phase.complete': 'COMPLETE',
        'windshield.id': 'WINDSHIELD #',
        'theme.toggle': 'Toggle theme',
        'readings.count': 'Readings',
    },
    fr: {
        'app.title': 'TRAÇABILITÉ ALIMENTATION',
        'app.subtitle': 'Système de contrôle qualité pare-brise',
        'config.title': 'Paramètres de Configuration',
        'config.model': 'MODÈLE',
        'config.tension': 'TENSION (V)',
        'config.intensity': 'INTENSITÉ (A)',
        'config.min': 'MIN.',
        'config.max': 'MAX.',
        'config.cycle': 'T. CYCLE (S)',
        'action.start': 'DÉMARRER LE TEST',
        'action.reset': 'RÉINITIALISER',
        'progress.title': 'PROGRESSION DE MESURE',
        'metrics.intensity': 'INTENSITÉ ACTUELLE (A)',
        'metrics.resistance': 'RÉSISTANCE (Ω)',
        'result.title': 'RÉSULTAT',
        'result.ok': 'CONFORME',
        'result.error': 'NON CONFORME',
        'result.pending': 'EN ATTENTE',
        'sticker.title': 'ÉTIQUETTE GÉNÉRÉE',
        'sticker.model': 'MODÈLE',
        'sticker.intensity': 'INTENSITÉ',
        'sticker.resistance': 'RÉSISTANCE',
        'sticker.date': 'DATE',
        'sticker.time': 'HEURE',
        'sticker.status': 'STATUT',
        'sticker.approved': 'APPROUVÉ',
        'phase.standby': 'EN ATTENTE',
        'phase.detecting': 'DÉTECTION DU PARE-BRISE',
        'phase.measuring': 'MESURE D\'INTENSITÉ',
        'phase.evaluating': 'ÉVALUATION DE CONFORMITÉ',
        'phase.complete': 'TERMINÉ',
        'windshield.id': 'PARE-BRISE N°',
        'theme.toggle': 'Changer le thème',
        'readings.count': 'Lectures',
    }
};

@Injectable({ providedIn: 'root' })
export class TranslateService {
    currentLang = signal<Lang>('es');

    constructor() {
        const saved = localStorage.getItem('wt-lang') as Lang;
        if (saved && TRANSLATIONS[saved]) {
            this.currentLang.set(saved);
        }
    }

    setLang(lang: Lang) {
        this.currentLang.set(lang);
        localStorage.setItem('wt-lang', lang);
    }

    t(key: string): string {
        return TRANSLATIONS[this.currentLang()]?.[key] ?? key;
    }
}
