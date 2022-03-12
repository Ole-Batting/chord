import numpy as np
import matplotlib.pyplot as plt
import os

class Guitar:
    def __init__(self, n_strings=6, n_frets=12, n_span=3, min_strings=4, max_fingers=4, top_mute=True, 
                 bottom_mute=True, tuning=['E4','B3','G3','D3','A2','E2'], path='figs'):
        
        assert n_strings >= min_strings, 'n_strings must be greater than or equal to min_strings'
        assert n_frets >= n_span, 'n_frets must be greater than or equal to n_span'
        assert n_strings >= max_fingers, 'n_strings must be greater than or equal to max_fingers'
        assert min_strings >= max_fingers, 'min_strings must be greater than or equal to max_fingers'
        
        self.path = path
        
        self.n_strings = n_strings
        self.n_frets = n_frets
        self.n_span = n_span
        self.min_strings = min_strings
        self.max_fingers = max_fingers
        self.top_mute = top_mute
        self.bottom_mute = bottom_mute
        self.tuning = tuning
        
        self.tone_dict = {
            'C': 0, 'C#': 1,
            'Db': 1, 'D': 2, 'D#': 3,
            'Eb': 3, 'E': 4,
            'F': 5, 'F#': 6,
            'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10,
            'Bb': 10, 'B': 11
        }
        self.note_list = [
            'C','C#','D','D#','E','F','F#','G','G#','A','A#','B'
        ]
        self.chord_base_dict = {
            'M': np.array([0,4,7]),
            'M7': np.array([0,4,7,11]),
            'maj7': np.array([0,4,7,11]),
            'm': np.array([0,3,7]),
            'm7': np.array([0,3,7,10]),
            'dim': np.array([0,3,6]),
            'dim7': np.array([0,3,6,9]),
            'aug': np.array([0,4,8]),
            'aug7': np.array([0,4,8,11]),
            '7': np.array([0,4,7,10]),
            'mM7': np.array([0,3,7,11])
        }
        
        self.open_strings = np.array([self.ipn_to_number(a) for a in self.tuning])
        self.fret_board = np.ones((self.n_strings, self.n_frets)) * np.arange(self.n_frets) + self.open_strings.reshape(-1,1)
        self.tone_board = self.fret_board % 12
    
    def __call__(self, chord, with_inversion=False, store_figs=False):
        self.chord_print(chord, with_inversion, store_figs=store_figs)
    
    def ipn_to_number(self, ipn):
        octave = int(ipn[-1])
        tone = self.tone_dict[ipn[:-1]]
        return octave * 12 + tone
    
    def number_to_ipn(self, number):
        octave = number // 12
        tone = number % 12
        return self.note_list[tone] + str(octave)
    
    def tone_on_board(self, tone):
        return self.tone_board == self.tone_dict[tone]
    
    def chord_to_list(self, chord):
        index = 2 if chord[1] in ['#', 'b'] else 1
        tone = chord[:index]
        extension = chord[index:]
        return [self.note_list[i] for i in (self.tone_dict[tone] + self.chord_base_dict[extension]) % 12]
    
    def chord_board(self, chord):
        return np.sum(np.array([self.tone_on_board(tone) for tone in chord]), axis=0)
    
    def expand_tree(self, voicings, tree, depth, chord):
        if depth == 6:
            voicings.append(chord)
        else:
            for branch in tree[depth]:
                self.expand_tree(voicings, tree, depth+1, [*chord, branch])
        if not depth:
            return np.array(voicings)

    def legal_mute(self, voicing):
        voiced = []
        muted = []
        for i, p in enumerate(voicing):
            if p == -1:
                muted.append(i)
            else: 
                voiced.append(i)
        return not any([s < max(voiced) and s > min(voiced) for s in muted])

    def chord_represented(self, voicing, chord):
        voiced_tones = (voicing[voicing != -1] + self.open_strings[voicing != -1]) % 12
        return all([self.tone_dict[tone] in voiced_tones for tone in chord])

    def voicing_not_in_voicings(self, voicing, voicings):
        return not next((True for elem in voicings if np.array_equal(elem, voicing)), False)

    def inversion_sort(self, voicings, chord):
        inversions = []
        for i in chord:
            inversions.append([])
            for j in voicings:
                if min(j[j!=-1] + self.open_strings[j!=-1]) % 12 == self.tone_dict[i]: #corrected to not just looking at lowest string
                    inversions[-1].append(j)
        return inversions

    def _chord_voicings(self, chord):
        board = self.chord_board(chord)
        voicings = []
        for fret in range(1, self.n_frets - self.n_span + 1):
            string_frets = []
            valid = True
            for string in range(self.n_strings):
                string_frets.append([])
                if board[string, 0]:
                    string_frets[string].append(0)
                if (self.top_mute and string >= self.min_strings) or (self.bottom_mute and string < self.n_strings - self.min_strings):
                    string_frets[string].append(-1)
                if 1 in board[string, fret:fret+self.n_span]:
                    for k in range(fret, fret + self.n_span):
                        if board[string, k]:
                            string_frets[string].append(k)
                if not string_frets[string]:
                    valid = False
            if valid:
                for voicing in self.expand_tree([], string_frets, 0, []):
                    if all([
                        len(voicing[voicing > 0]) <= self.max_fingers,
                        len(voicing[voicing >= 0]) >= self.min_strings,
                        self.legal_mute(voicing),
                        self.chord_represented(voicing, chord),
                        self.voicing_not_in_voicings(voicing, voicings)
                    ]):
                        voicings.append(voicing)
        inversions = self.inversion_sort(voicings, chord)
        self.rich_sort(inversions)
        return inversions
    
    def chord_voicings(self, chord):
        return self.chord_voicings(self.chord_to_list(chord))
    
    def plot_cross(self, i, radius = 0.3, ax=None):
        x1 = [i - radius * 0.7, i + radius * 0.7]
        x2 = [i + radius * 0.7, i - radius * 0.7]
        y = [0.5 - radius * 0.7, 0.5 + radius * 0.7]
        if ax==None:
            plt.plot(x1, y, 'black')
            plt.plot(x2, y, 'black')
        else:
            ax.plot(x1, y, 'black')
            ax.plot(x2, y, 'black')
    
    def chord_plot(self, chord, name, ext=5, radius = 0.3, store_figs=False):
        
        n_ext = max(self.n_span, ext)
        fr = 1 if np.max(chord) <= n_ext else np.min(chord[chord > 0])
        fig, ax = plt.subplots(figsize=(4,4))
        
        # fret grid
        for i in range(self.n_strings):
            plt.plot([i, i], [0, -n_ext], 'black')
        for i in range(n_ext + 1):
            plt.plot([0, self.n_strings - 1], [-i, -i], 'black',
                     linewidth = 5 if i==0 and fr==1 else None)

        # finger positions
        for i, c in enumerate(np.flip(chord)):
            x = i
            y = fr - c - 0.5 if c > 0 else 0.5
            if c == -1:
                self.plot_cross(i, radius)
                plt.text(x - 0.2, -5.5, 
                         self.number_to_ipn(np.flip(self.open_strings)[i]), 
                         color = 'gray')
            else:
                ax.add_patch(plt.Circle((x,y), radius, color='black', fill=c!=0))
                plt.text(x - 0.2, -5.5, 
                         self.number_to_ipn(c + np.flip(self.open_strings)[i]))
        # starting fret
        if fr != 1:
            plt.text(-0.3 * len(str(fr)) - 0.4, -0.68, f'{fr}', fontsize='xx-large')

        ax.axis('off')
        ax.axis('equal')
        plt.title(name.replace("M7","maj7").replace("M", ""))
        if store_figs:
            path = f'{self.path}/{name.replace("/","_over_").replace("M","")}'
            if not os.path.isdir(path):
                os.mkdir(path)
            plt.savefig(f'{path}/{chord}.png', dpi=300)
        plt.show()
        
    def chord_plot_open(self, chord, name, ext=5, radius = 0.3, store_figs=False, ax=None):
        
        n_ext = max(self.n_span, ext)
        fr = 1 if np.max(chord) <= n_ext else np.min(chord[chord > 0])
        if ax==None: 
            fig, ax = plt.subplots(figsize=(4,4))
        
        # fret grid
        for i in range(self.n_strings):
            x = [i, i]
            y = [0, -n_ext]
            ax.plot(x, y, 'black')
        for i in range(n_ext + 1):
            x = [0, self.n_strings - 1]
            y = [-i, -i]
            ax.plot(x, y, 'black', linewidth = 5 if i==0 and fr==1 else None)

        # finger positions
        for i, c in enumerate(np.flip(chord)):
            if c == -2:
                continue
            x = i
            y = fr - c - 0.5 if c > 0 else 0.5
            if c == -1:
                self.plot_cross(i, radius, ax=ax)
                ax.text(x - 0.2, -5.5, self.number_to_ipn(np.flip(self.open_strings)[i]), color='gray')
            else:
                ax.add_patch(plt.Circle((x,y), radius, color='black', fill=c!=0))
                ax.text(x - 0.2, -5.5, self.number_to_ipn(c + np.flip(self.open_strings)[i]))
        if fr != 1:
            x = -0.3 * len(str(fr)) - 0.4
            y = -0.68
            ax.text(x, y, f'{fr}', fontsize='xx-large')
        ax.axis('off')
        ax.axis('equal')
        ax.set_title(name.replace("M7","maj7").replace("M", ""))
    
    def chord_print(self, chord, with_inversion=False, store_figs=False):
        manual = type(chord) is list
         
        if not manual:
            chord_list = self.chord_to_list(chord)
            for i, inv in enumerate(self._chord_voicings(chord_list)):
                if not i or with_inversion:
                    for c in inv:
                        if not i:
                            name = chord
                        else:
                            name = f'{chord}/{chord_list[i]}'
                        self.chord_plot(c, name, store_figs=store_figs)
        else:
            for i, inv in enumerate(self._chord_voicings(chord)):
                if not i or with_inversion:
                    for c in inv:
                        self.chord_plot(c, '-'.join(chord), store_figs=store_figs)
    
    def fret_sort(self, elem):
        if len(elem[elem>0]>0):
            return np.mean(elem[elem>0])
        else:
            return 0
    
    def mute_sort(self, elem):
        # max because we dont care if one or (but slightly) two of the upper strings are muted
        return max(self.n_strings * len(elem[elem==-1]) - np.sum(np.argwhere(elem==-1)), 2)
    
    def finger_sort(self, elem):
        return len(elem[elem>0])
    
    def rough_finger_sort(self, elem):
        return max(len(elem[elem>0]), 3)

    def rich_sort(self, positions):
        #sort min fret
        #sort muted strings
        for p in positions:
            p.sort(key=self.finger_sort)
            p.sort(key=self.fret_sort)
            p.sort(key=self.mute_sort)
            p.sort(key=self.rough_finger_sort)
    
    def tuning_stats(self):
        chords = [
            'CM','C#M','DM','D#M','EM','FM','F#M','GM','G#M','AM','A#M','BM',
            'Cm','Dbm','Dm','Ebm','Em','Fm','Gbm','Gm','Abm','Am','Bbm','Bm'
        ]
        stats = {'m': 0, 'f': 0, 'r': 0}
        for chord in chords:
            positions = self.chord_voicings(chord)[0]
            if positions:
                p = positions[0]
                stats['m'] += len(p[p==-1]) # lower is better
                stats['f'] += len(p[p>0]) # lower is better
                stats['r'] += self.mute_sort(p) # lower is better
            else:
                return False, None
        return True, stats
    
    def tuning_gain(self):
        chords = [
            'CM','C#M','DM','D#M','EM','FM','F#M','GM','G#M','AM','A#M','BM',
            'Cm','Dbm','Dm','Ebm','Em','Fm','Gbm','Gm','Abm','Am','Bbm','Bm',
        ]
        weights = np.array([
            0.6084,0.1638,0.1872,0.2340,0.1638,0.2106,
            0.0702,0.2808,0.0936,0.1872,0.1170,0.0702,
            0.2574,0.0693,0.0792,0.0990,0.0693,0.0891,
            0.0297,0.1188,0.0396,0.0792,0.0495,0.0297,
        ])
        stats = {'m': 0, 'f': 0, 'r': 0, 'v': 0}
        for chord, weight in zip(chords, weights):
            positions = self.chord_voicings(chord)[0]
            if positions:
                p = positions[0]
                stats['m'] += weight * len(p[p==-1]) # lower is better
                stats['f'] += weight * len(p[p>0]) # lower is better
                stats['r'] += weight * self.mute_sort(p) # lower is better
                stats['v'] += weight * len(positions)
            else:
                return False, None
        return True, stats
    
    def mute_equal(self, c1, c2):
        for i in range(len(c1)):
            if c1[i]!=c2[i] and c1[i]!=-1 and c2[i]!=-1:
                return False
        return True
    
    def collage(self, chord):
        chord_list = self.chord_to_list(chord)
        chord7_list = self.chord_to_list(chord+'7')

        inversions = self._chord_voicings(chord_list)
        inversions7 = self._chord_voicings(chord7_list)
        for i, positions in enumerate(inversions):
            fig, axs = plt.subplots(1, 3, figsize=(12,4))
            if not i:
                name = chord
            else:
                name = f'{chord}/{chord_list[i]}'
            
            P = []
            for c in positions:
                if any([self.mute_equal(c, c2) for c2 in P]):
                    continue
                P.append(c)
                self.chord_plot_open(c, name, ax=axs[len(P)-1])
                if len(P)==3:
                    break
                    
            path = f'{self.path}/{name.replace("/","_over_").replace("M7","maj7").replace("M","")}'
            if not os.path.isdir(path):
                os.mkdir(path)
            plt.savefig(f'{path}/{name.replace("/","_over_")}_collage.png', dpi=300)
            plt.show()

        fig, axs = plt.subplots(1, 3, figsize=(12,4))
        name = chord+'7'
        
        P = []
        for j, c in enumerate(inversions7[0]):
            if any([self.mute_equal(c, c2) for c2 in P]):
                continue
            P.append(c)
            self.chord_plot_open(c, name, ax=axs[len(P)-1])
            if len(P)==3:
                break
        path = f'{self.path}/{name.replace("/","_over_").replace("M7","maj7").replace("M","")}'
        if not os.path.isdir(path):
            os.mkdir(path)
        plt.savefig(f'{path}/{name.replace("/","_over_")}_collage.png', dpi=300)
        plt.show()
    
    def poster(self, chord):
        fig, axs = plt.subplots(4, 3, figsize=(12,16))
        chord_list = self.chord_to_list(chord)
        chord7_list = self.chord_to_list(chord+'7')

        inversions = self._chord_voicings(chord_list)
        inversions7 = self._chord_voicings(chord7_list)
        for i, positions in enumerate(inversions):
            if not i:
                name = chord
            else:
                name = f'{chord}/{chord_list[i]}'
            
            P = []
            for c in positions:
                if any([self.mute_equal(c, c2) for c2 in P]):
                    continue
                P.append(c)
                self.chord_plot_open(c, name, ax=axs[i,len(P)-1])
                if len(P)==3:
                    break

        name = chord+'7'
        
        P = []
        for j, c in enumerate(inversions7[0]):
            if any([self.mute_equal(c, c2) for c2 in P]):
                continue
            P.append(c)
            self.chord_plot_open(c, name, ax=axs[3,len(P)-1])
            if len(P)==3:
                break
        path = f'{self.path}/{chord.replace("M","")}'
        if not os.path.isdir(path):
            os.mkdir(path)
        plt.savefig(f'{path}/{chord.replace("M","")}_poster.png', dpi=300)
        plt.show()
