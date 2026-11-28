#include "resident_input_private_3.h"

/* C483: selectors reread flags at each decision, no cached global
 * snapshot. Each priority chain retains the literal first-match rule. */
PcmStatus pcm_resident_input_c483(Pcm *pcm)
{
    bool set;
    uint8_t v;
    SYS_RUN(test(pcm,0x9f,4,&set));
    if(set) v=1;
    else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?2:4; }
    SYS_RUN(pcm_write8(pcm,0x80,v));
    SYS_RUN(test(pcm,0x9f,4,&set));
    SYS_RUN(pcm_write8(pcm,0x82,set?1:2));
    SYS_RUN(test(pcm,0x87,2,&set));
    if(set) v=1;
    else {
        SYS_RUN(test(pcm,0x9f,4,&set));
        if(set) v=2;
        else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?4:8; }
    }
    SYS_RUN(pcm_write8(pcm,0x7f,v));
    SYS_RUN(test(pcm,0x87,4,&set));
    if(set) v=1;
    else {
        SYS_RUN(test(pcm,0x87,2,&set));
        if(set) v=2;
        else {
            SYS_RUN(test(pcm,0x9f,4,&set));
            if(set) v=4;
            else { SYS_RUN(test(pcm,0x9f,2,&set)); v=set?8:16; }
        }
    }
    return pcm_write8(pcm,0x81,v);
}
