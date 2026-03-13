import { Pipe, PipeTransform } from '@angular/core';
import { TranslateService } from '../services/translate.service';

@Pipe({
    name: 'translate',
    standalone: true,
    pure: false // Impure so it re-evaluates when language changes
})
export class TranslatePipe implements PipeTransform {
    constructor(private translateService: TranslateService) { }

    transform(key: string): string {
        return this.translateService.t(key);
    }
}
