import time, os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait, Select
from clients.digisac import Digisac

load_dotenv() # carrega CPF/SENHA/NUMBER do .env

class Pan:
    def __init__(self):
        # conecta ao Edge já aberto no modo remote-debugging (127.0.0.1:9222
        self.options = Options()
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Edge(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.digisac = Digisac() # cliente pra enviar mensagens
    
    def _send_keys(self, by: str, value: str, keys: str) -> None:
        # espera elemento, clica se habilitado e envia keys.
        try:
            element = self.wait.until(expected_conditions.presence_of_element_located((by, value)))

            if element.is_enabled():
                element.click()
                element.send_keys(keys)
        except:
            pass
    
    def _click(self, by: str, value: str) -> None:
        # espera elemento clicável e clica via JS.
        try:
            element = self.wait.until(expected_conditions.element_to_be_clickable((by, value)))

            if element.is_enabled():
                self.driver.execute_script("arguments[0].click();", element)
        except:
            pass
    
    def _alert(self) -> None:
        # aceita alert JS se aparecer
        try:
            alert = self.wait.until(expected_conditions.alert_is_present())
            alert.accept()
        except:
            pass

    def get_link(self) -> None:
        # abre a página principal
        self.driver.get("https://panconsig.pansolucoes.com.br/WebAutorizador/")
    
    def auth(self) -> None:
        # faz login: CPF, escolhe parceiro e tenta senha (senha pode não aparecer sempre)
        self._send_keys(By.CSS_SELECTOR, "#cpf-input > label > span.mahoe-input__input > input[type=text]", os.getenv("CPF"))
        self._click(By.ID, "form-partner-value")
        self._click(By.ID, "form-partner-0")
        self._click(By.CSS_SELECTOR, "button.mahoe-button__primary")
        
        try:
            self._send_keys(By.CSS_SELECTOR, "#senha > label > span.mahoe-input__input > input[type=password]", os.getenv("SENHA"))
            self._click(By.CSS_SELECTOR, "button.mahoe-button__primary")  
        except:
            pass       

    def FlMenu(self) -> None:
        # lida com menu que pode estar fechado ou com página de erro
        while True:
            url = self.driver.current_url

            try:
                if "Erro.aspx" in url:
                    self._click(By.ID, "lnkVoltar")

                    break
                else:
                    div = self.driver.find_element(By.CSS_SELECTOR, "div.fechado.naoClicavel")

                    if div:
                        break
            except:
                pass
        
        # força exibir o menu e clica no link dentro
        self.driver.execute_script("arguments[0].style.display = 'block';", div)
        self._click(By.CSS_SELECTOR, "#block > a")

    def WebAutorizador(self) -> None:
        # navega no menu por hover e clica em "Consulta Não Me Perturbe"
        menu_cadastro = self.wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//a[contains(., 'Cadastro') and contains(@class, 'dropdown-toggle')]")))
        ActionChains(self.driver).move_to_element(menu_cadastro).perform()

        consulta_nao_me_perturbe = self.wait.until(expected_conditions.visibility_of_element_located((By.XPATH, "//a[@href='/WebAutorizador/Cadastro/CardOferta' and contains(., 'Consulta Não Me Perturbe')]")))
        self.driver.execute_script("arguments[0].click();", consulta_nao_me_perturbe)

    def CardOferta(self, cpf: str, ddd: str, phone: str) -> None:
        # preenche formulário de oferta: empregador, CPF, DDD e telefone
        self.driver.refresh()

        select_empregador = self.wait.until(expected_conditions.presence_of_element_located((By.ID, "Empregador")))
        select = Select(select_empregador)
        time.sleep(1)
        select.select_by_value("000577")

        self._send_keys(By.ID, "CPF", cpf)

        ddd_input = self.driver.find_element(By.ID, "DDD")
        ddd_input.click()
        time.sleep(1)
        ddd_value = ddd_input.get_attribute("value")
        
        # só insere DDD/telefone se campo estiver vazio
        if not ddd_value:
            ddd_input.send_keys(ddd)

            self._send_keys(By.ID, "Telefone", phone)
        
        self._click(By.ID, "btnAceiteAutorizacaoCPD")

    def get_farol_title(self) -> str:
        # lê o status e retorna título; se aparecer diálogo retorna texto do diálogo
        time.sleep(1)

        while True:
            farol = self.driver.find_element(By.ID, "farolSolicitacaoId")
            title = farol.get_attribute("title")

            if not title:
                try:
                    time.sleep(1)
                    alert_div = self.wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ui-dialog-content")))

                    return alert_div.text
                except:
                    pass
            
            # se já tiver um título final retorna
            if title not in ["Aguardando Resposta", "Aguardando Retorno"]:
                return title
            
            # tenta reenviar o aceite se ainda estiver em espera
            try:
                self._click(By.ID, "btnAceiteAutorizacaoCPD")
            except Exception as exception:
                print(f"[GET_FAROL_TITLE (EXCEPTION)]: {exception}")

    def locate(self, data: dict) -> bool:
        # roteador simples: chama função conforme URL atual; retorna True se ficou em CardOferta
        url = self.driver.current_url
        
        if "CardOferta" in url:
            self.CardOferta(data["cpf"], data["ddd"], data["telefone"])
            
            return True
        elif "WebAutorizador" in url:
            self.WebAutorizador()
        elif any(option in url for option in ["FIMENU", "FlMenu"]):
            self.FlMenu()
        elif "auth" in url:
            self.auth()
            self.get_link_login()
        else:
            self.get_link()
        
        return False
    
    def get_link_login(self) -> None:
        # busca link do QR de login e envia via digisac se válido
        try:
            link_element = self.wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "a.qr-code__link[href]")))
            link = (link_element.get_attribute("href") or "").strip()

            if link.startswith("http"):
                self.digisac.send_message(f"Link pro login do PAN: {link}", os.getenv("NUMBER"))
        except:
            pass

    def consult(self) -> str | list:
        # tenta consulta rápida; se não retorna texto do modal, simula cenários e retorna lista de ofertas
        time.sleep(3)
        self._click(By.ID, "btnConsultar")
        self._click(By.ID, "btnOfertarMargemLivre")

        try: 
            div = self.wait.until(expected_conditions.visibility_of_element_located((By.ID, "ui-id-1")))
                
            return div.text.strip() # erro / modal com informação
        except:
            pass

        self._alert()
        
        data = []

        self.simulate(data)

        # se não encontrou nenhuma oferta tenta ajustar parcela (reduz R$5,00)
        if len(data) == 0:
            valor_parcela_input = self.wait.until(expected_conditions.presence_of_element_located((By.ID, "ctl00_Cph_ucP_JN_JpSim_txtVlrParc_CAMPO")))
            valor_parcela_input_value = valor_parcela_input.get_attribute("value")
            adjusted_value = float(valor_parcela_input_value.replace(",", ".")) - 5 # converte vírgula para ponto e subtrai
            
            valor_parcela_input.click()
            valor_parcela_input.send_keys(str(adjusted_value).replace(".", ","))
            self.simulate(data)
        
        self.get_link()

        return data       

    def simulate(self, data: list) -> None:
        # percorre prazos fixos, calcula e coleta ofertas válidas na tabela
        periods = ["48", "42", "36", "30", "24", "18", "12", "6"]

        for period in periods:
            period_dropdown = self.wait.until(expected_conditions.element_to_be_clickable((By.ID, "ctl00_Cph_ucP_JN_JpSim_cbPrz_CAMPO")))
            Select(period_dropdown).select_by_value(period)

            self._click(By.ID, "btnCalcular_txt")
                
            try:
                old_table = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_gvCond")
            except:
                old_table = None

            # espera a tabela antiga sumir antes de ler nova
            if old_table:
                try:
                    self.wait.until(expected_conditions.staleness_of(old_table))
                except TimeoutException:
                    pass
                
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_Cph_ucP_JN_JpSim_gvCond tr.normal, #ctl00_Cph_ucP_JN_JpSim_gvCond tr.alternate")
                num = len(rows)

                for i in range(num):
                    try:
                        rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_Cph_ucP_JN_JpSim_gvCond tr.normal, #ctl00_Cph_ucP_JN_JpSim_gvCond tr.alternate")
                        row = rows[i]
                        cells = row.find_elements(By.TAG_NAME, "td")

                        if len(cells) > 5:
                            raw = cells[5].text.strip()
                            value = float(raw.replace(".", "").replace(",", ".")) # formata valor pra float

                            if value > 0.0:
                                # marca checkbox da linha e captura dados da oferta
                                checkbox = row.find_element(By.TAG_NAME, "input")
                                self.driver.execute_script("arguments[0].click();", checkbox)

                                self._alert()

                                # espera tabela de financiamento aparecer e lê spans
                                self.wait.until(expected_conditions.visibility_of_element_located((By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc")))
                                span_parcela = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc_ctl03_lVlr")
                                span_prazo = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc_ctl05_lVlr")
                                span_liberado = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucDSP_grdDespesas_ctl04_Label1")
                                    
                                valor_parcela = span_parcela.text.strip()
                                prazo = span_prazo.text.strip()
                                valor_liberado = span_liberado.text.strip()
                                    
                                data.append({
                                    "parcela": valor_parcela,
                                    "liberado": valor_liberado,
                                    "prazo": prazo
                                })

                    except Exception as exception:
                        print(f"[EXCEPTIION]: {exception}")
            except:
                pass    