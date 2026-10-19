#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Protocolo peticion-respuesta entre dos procesos usando sockets UDP.

Protocolos implementados:
  - 2 vias: REQUEST -> RESPONSE
  - 3 vias: REQUEST -> RESPONSE -> ACK
  - 4 vias: REQUEST -> RESPONSE -> CONFIRM -> ACK

Requisito cumplido: cada proceso ENVIA y RECIBE en puertos distintos.
    Proceso A: recibe en 54000, envia desde 54002 hacia B (54001)
    Proceso B: recibe en 54001, envia desde 54003 hacia A (54000)

Uso (dos terminales):
    Terminal 1: python protocolo.py B 2    # responde (debe iniciarse primero)
    Terminal 2: python protocolo.py A 2    # inicia la peticion

    Cambie el ultimo argumento a 3 o 4 para probar esos protocolos.
"""

import socket
import json
import sys

HOST = "127.0.0.1"

# Cada proceso tiene un puerto distinto para recibir y para enviar.
PORTS = {
    "A": {"recv": 54000, "send": 54002, "peer_recv": 54001},
    "B": {"recv": 54001, "send": 54003, "peer_recv": 54000},
}

# Tipos de mensaje
REQUEST = "REQUEST"
RESPONSE = "RESPONSE"
ACK = "ACK"
CONFIRM = "CONFIRM"


def make_msg(mtype, seq, payload=""):
    """Codifica un mensaje como JSON."""
    return json.dumps({"type": mtype, "seq": seq, "payload": payload}).encode("utf-8")


def parse_msg(data):
    """Decodifica un mensaje JSON."""
    return json.loads(data.decode("utf-8"))


class Proceso:
    def __init__(self, rol, proto):
        self.rol = rol
        self.proto = int(proto)
        p = PORTS[rol]
        self.recv_port = p["recv"]
        self.send_port = p["send"]
        self.peer_recv = p["peer_recv"]

        # Socket dedicado para RECIBIR (vinculado a recv_port)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recv_sock.bind((HOST, self.recv_port))
        self.recv_sock.settimeout(5.0)

        # Socket dedicado para ENVIAR (vinculado a send_port, distinto al de recibo)
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.send_sock.bind((HOST, self.send_port))

        self.seq = 0

    def enviar(self, mtype, payload=""):
        self.seq += 1
        msg = make_msg(mtype, self.seq, payload)
        self.send_sock.sendto(msg, (HOST, self.peer_recv))
        print(f"[{self.rol}] envia {mtype} (seq={self.seq}) "
              f"puerto {self.send_port} -> {self.peer_recv}")

    def recibir(self):
        data, addr = self.recv_sock.recvfrom(4096)
        msg = parse_msg(data)
        print(f"[{self.rol}] recibe {msg['type']} (seq={msg['seq']}) "
              f"desde {addr} en puerto {self.recv_port}")
        return msg

    def cerrar(self):
        self.recv_sock.close()
        self.send_sock.close()

    def rol_A(self):
        """Proceso iniciador: envia la primera peticion."""
        self.enviar(REQUEST)
        msg = self.recibir()
        if msg["type"] != RESPONSE:
            raise RuntimeError(f"Se esperaba RESPONSE, llego {msg['type']}")

        if self.proto >= 3:
            self.enviar(ACK if self.proto == 3 else CONFIRM)

        if self.proto == 4:
            msg = self.recibir()
            if msg["type"] != ACK:
                raise RuntimeError(f"Se esperaba ACK, llego {msg['type']}")

        print(f"[{self.rol}] Protocolo de {self.proto} vias completado (EXITO)")

    def rol_B(self):
        """Proceso respondedor: espera la peticion inicial."""
        msg = self.recibir()
        if msg["type"] != REQUEST:
            raise RuntimeError(f"Se esperaba REQUEST, llego {msg['type']}")
        self.enviar(RESPONSE)

        if self.proto >= 3:
            msg = self.recibir()
            expected = ACK if self.proto == 3 else CONFIRM
            if msg["type"] != expected:
                raise RuntimeError(f"Se esperaba {expected}, llego {msg['type']}")

        if self.proto == 4:
            self.enviar(ACK)

        print(f"[{self.rol}] Protocolo de {self.proto} vias completado (EXITO)")

    def ejecutar(self):
        if self.rol == "A":
            self.rol_A()
        else:
            self.rol_B()


def main():
    if len(sys.argv) != 3:
        print("Uso: python protocolo.py <A|B> <2|3|4>")
        print("  A = iniciador, B = respondedor (iniciar B primero)")
        print("  2|3|4 = cantidad de vias del protocolo")
        sys.exit(1)

    rol = sys.argv[1].upper()
    proto = sys.argv[2]
    if rol not in ("A", "B") or proto not in ("2", "3", "4"):
        print("Argumentos invalidos. Role: A|B, Proto: 2|3|4")
        sys.exit(1)

    proc = Proceso(rol, proto)
    try:
        proc.ejecutar()
    except socket.timeout:
        print(f"[{rol}] Timeout: no se recibio un mensaje esperado.")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"[{rol}] Error: {e}")
        sys.exit(1)
    finally:
        proc.cerrar()


if __name__ == "__main__":
    main()
